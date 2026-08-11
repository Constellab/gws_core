"""An OAuth 2.1 authorization server for the lab.

This is the lab's general authorization server: it authorizes **any** OAuth client
(the MCP endpoint is simply its first consumer) entirely on its own -- no Space, no
Community, no password, and the browser never leaves the lab's own domains::

    +----------+     +-------------+     +-------------------+
    | a client | --> | lab API     | --> | lab front-end     |
    |          |     | (this file) |     | consent page      |
    +----------+     +-------------+     +-------------------+

The token it issues is a **lab JWT** -- the one :class:`JWTService` signs with the
lab's ``secret_key`` and every lab route already validates -- so a client can call
the lab as the user who consented.

The user is already logged into the lab front-end, so identity needs no new
credential: the consent page proves who they are with a single-use code from
``UniqueCodeService`` (the same bridge the lab uses for ``login-temp-access``,
needed because the front-end and API sit on different sub-domains and the session
cookie is ``samesite=strict``).

.. warning::
   **Tokens are currently unscoped**: an issued token is a full lab session, able
   to do anything its user can, whatever the consent screen said the client wanted.
   That is tolerable while the only consumer is the read-only MCP endpoint, but any
   second consumer -- and certainly any third-party client -- needs real scopes
   first. The plumbing is ready for them: ``scopes`` is carried end to end
   (``AuthorizationParams`` -> ``AuthorizationCode`` -> ``AccessToken``) and
   :meth:`_mint_lab_token` is the single place that turns a grant into a token.
   :meth:`JWTService.create_app_jwt` already shows how the lab mints a *bounded*
   token (``typ``/``app_id`` claims, refused on normal user routes).

Why the MCP SDK types
---------------------
The ``mcp.server.auth`` package is used for the protocol machinery, but nothing
here is MCP-specific: those classes are plain pydantic models of the OAuth RFCs
(``code_challenge``, ``refresh_token``, ...) and its ``create_auth_routes`` serves a
standard OAuth surface -- discovery, ``/register`` (DCR), ``/authorize``, ``/token``,
PKCE verification, redirect_uri validation -- all driven by the provider below.
Reusing it avoids hand-rolling an authorization server; a different transport can
use this provider without involving MCP.

This class supplies only the lab-specific behaviour:

- ``authorize``               -> point the browser at the lab's consent page
- ``complete_authorization``  -> once consent is given, mint an authorization code
                                 and redirect back to the client
- ``exchange_*``              -> mint the lab JWT as the OAuth access token

Registered clients are persisted (see :mod:`oauth_client`). The rest of the state
(pending logins, authorization codes, refresh tokens) is in memory: it is
short-lived, and losing it on a restart only costs a login retry.
"""

import secrets
import time
from dataclasses import dataclass, field

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    TokenError,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from gws_core.core.utils.logger import Logger
from gws_core.oauth.oauth_client import OAuthClient
from gws_core.oauth.oauth_dto import OAuthConsentDetailsDTO
from gws_core.user.authorization_service import AuthorizationService
from gws_core.user.jwt_service import JWTService
from gws_core.user.user import User
from gws_core.user.user_service import UserService

# How long a minted authorization code stays usable (OAuth codes are short-lived).
AUTHORIZATION_CODE_TTL_SECONDS = 5 * 60

# How long a pending browser login may stay unfinished before being dropped.
PENDING_LOGIN_TTL_SECONDS = 10 * 60

# How long a refresh token stays valid. Longer than the 2-day access token so a
# regularly-used client is not sent back to the browser, but bounded so an
# abandoned credential cannot be replayed indefinitely.
REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60

# Whether an issued token is limited to the scopes it was granted.
#
# False today: ``_mint_lab_token`` issues a full lab session, so a client can do
# anything its user can. This single flag is what the consent page's wording is
# derived from (``_describe_access``), so the screen cannot claim a narrower grant
# than the lab actually gives. Flip it -- and bind the scopes in
# ``_mint_lab_token`` -- when scope enforcement lands; the consent page follows on
# its own.
SCOPES_ARE_ENFORCED = False


@dataclass
class _PendingLogin:
    """An authorization opened by /authorize, awaiting the user's consent."""

    params: AuthorizationParams
    client_id: str
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        return time.time() - self.created_at > PENDING_LOGIN_TTL_SECONDS


def _require_client_id(client_info: OAuthClientInformationFull) -> str:
    """Return the client's id, which the SDK types as optional but always sets.

    ``client_id`` is only ``None`` on a metadata object that has not been through
    registration yet; every client the provider is handed has already been
    registered, so a missing id means the SDK broke its own contract.
    """
    if client_info.client_id is None:
        raise ValueError("The OAuth client has no client_id.")
    return client_info.client_id


class LabOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """The lab's OAuth 2.1 authorization server.

    One instance serves one protected resource. To authorize a second kind of
    client, build a second instance with that resource's URL rather than widening
    this one -- ``resource_url`` is the RFC 8707 identifier a token is bound to.

    :param consent_page_url: Absolute URL of the lab front-end's consent page,
        where the user approves the client.
    :param resource_url: Canonical URL of the resource being protected, echoed
        back on issued access tokens as the RFC 8707 resource indicator.
    :param resource_name: Human-readable name of that resource, shown to the user
        on the consent page (e.g. "MCP server").
    :param lab_url: The lab's base URL, shown on the consent page so a user with
        several labs can see which one they are authorizing.
    """

    def __init__(
        self,
        consent_page_url: str,
        resource_url: str,
        resource_name: str,
        lab_url: str,
    ) -> None:
        self._consent_page_url = consent_page_url
        self._resource_url = resource_url
        self._resource_name = resource_name
        self._lab_url = lab_url

        # Registered clients live in the DB (see OAuthClient): a client caches its
        # client_id forever, so an in-memory registry would break it for good on
        # the first lab restart. The rest of the state below is short-lived and is
        # fine to lose on a restart -- it only costs a login retry.
        #
        # keyed by the opaque state we hand to the callback
        self._pending_logins: dict[str, _PendingLogin] = {}
        self._auth_codes: dict[str, AuthorizationCode] = {}
        # authorization code -> lab user id, resolved during the callback
        self._code_user_ids: dict[str, str] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}

    # ------------------------------------------------------------------ #
    #  Client registration (Dynamic Client Registration)
    # ------------------------------------------------------------------ #

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        stored = OAuthClient.find_by_client_id(client_id)
        if stored is None:
            return None
        return OAuthClientInformationFull.model_validate(stored.client_info)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        OAuthClient.save_client(
            client_id=_require_client_id(client_info),
            client_info=client_info.model_dump(mode="json", exclude_none=True),
        )
        Logger.debug(f"OAuth: registered client '{client_info.client_id}'")

    # ------------------------------------------------------------------ #
    #  Authorization: hand the user to the lab's own consent page
    # ------------------------------------------------------------------ #

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Return the URL of the lab's consent page for this authorization.

        The client's OAuth parameters (PKCE challenge, redirect_uri, state)
        are stashed against an opaque ``login_state``, which is the only thing
        handed to the front-end. The SDK verifies the PKCE challenge later, at
        /token.
        """
        login_state = secrets.token_urlsafe(32)
        self._pending_logins[login_state] = _PendingLogin(
            params=params,
            client_id=_require_client_id(client),
        )
        self._prune_pending_logins()

        return construct_redirect_uri(self._consent_page_url, login_state=login_state)

    def complete_authorization(self, login_state: str, user: User) -> str:
        """Finish the flow for ``login_state``: mint a code, return the client redirect.

        Called by the consent route once the user has approved and been
        identified as a lab :class:`User`.

        :param login_state: The opaque state issued by :meth:`authorize`.
        :param user: The authenticated lab user.
        :return: The URL to redirect the client back to.
        :raises TokenError: If the login state is unknown or expired.
        """
        pending = self._pending_logins.pop(login_state, None)
        if pending is None or pending.is_expired():
            raise TokenError("invalid_request", "Login session expired. Please retry the login.")

        params = pending.params
        code = secrets.token_urlsafe(32)  # > 160 bits of entropy, per the spec

        self._auth_codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + AUTHORIZATION_CODE_TTL_SECONDS,
            client_id=pending.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
            subject=user.id,
        )
        self._code_user_ids[code] = user.id

        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    def get_pending_login(self, login_state: str) -> _PendingLogin | None:
        """Return the pending login for ``login_state``, if still valid."""
        pending = self._pending_logins.get(login_state)
        if pending is None or pending.is_expired():
            return None
        return pending

    async def get_consent_details(
        self, login_state: str, user: User
    ) -> OAuthConsentDetailsDTO | None:
        """Describe what ``login_state`` would authorize, for the consent page.

        The wording lives here rather than in the front-end because this is the only
        place that knows both which client is asking and what a token actually
        grants it. In particular ``access_level`` is **derived** from whether scopes
        are enforced, not hardcoded: when scoped tokens land, the consent page starts
        telling users the narrower truth with no front-end change.

        :param login_state: The opaque state issued by :meth:`authorize`.
        :param user: The user being asked to consent.
        :return: The details, or ``None`` if the request is unknown or expired.
        """
        pending = self.get_pending_login(login_state)
        if pending is None:
            return None

        client = await self.get_client(pending.client_id)
        if client is None:
            return None

        return OAuthConsentDetailsDTO(
            client_name=client.client_name or "Unnamed client",
            client_id=pending.client_id,
            # Registration is open, so the name is a self-declared claim. Nothing
            # verifies it today; the front-end must present it as untrusted.
            client_name_is_verified=False,
            resource_name=self._resource_name,
            lab_url=self._lab_url,
            user_email=user.email,
            **self._describe_access(pending.params.scopes),
        )

    @staticmethod
    def _describe_access(scopes: list[str] | None) -> dict:
        """Describe, in the user's terms, what the issued token will allow.

        Tokens are unscoped today: :meth:`_mint_lab_token` issues a full lab session,
        so a client can do anything its user can, regardless of what it asked for.
        Saying anything narrower on the consent screen (e.g. "read-only queries",
        which describes today's *tools*, not the *token*) would be false.

        When scope enforcement arrives, this branches on it and the page follows.
        """
        if not SCOPES_ARE_ENFORCED:
            return {
                "access_level": "full",
                "access_summary": "Act as you on this lab",
                "access_details": [
                    "Read and write anything your account can access",
                    "Run tools on your behalf",
                ],
                "warning": (
                    "This client will have the same permissions as your account "
                    "— it is not limited to a subset."
                ),
            }

        return {
            "access_level": "scoped",
            "access_summary": "Act as you on this lab, limited to what it asked for",
            "access_details": sorted(scopes or []),
            "warning": None,
        }

    # ------------------------------------------------------------------ #
    #  Token issuance: mint the lab JWT
    # ------------------------------------------------------------------ #

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        code = self._auth_codes.get(authorization_code)
        if code is None or code.client_id != client.client_id:
            return None
        if code.expires_at < time.time():
            self._forget_code(authorization_code)
            return None
        return code

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        """Exchange a validated authorization code for a lab JWT.

        The SDK has already verified the PKCE code_verifier and the redirect_uri
        by the time this runs.
        """
        user_id = self._code_user_ids.get(authorization_code.code)
        if user_id is None:
            raise TokenError("invalid_grant", "Unknown authorization code.")

        # Codes are single-use.
        self._forget_code(authorization_code.code)

        access_token = self._mint_lab_token(user_id, authorization_code.scopes)
        refresh_token = self._issue_refresh_token(
            client_id=_require_client_id(client),
            user_id=user_id,
            scopes=authorization_code.scopes,
        )

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=JWTService.get_token_duration_in_seconds(),
            refresh_token=refresh_token,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token presented by a client.

        The library derives its token verifier from this method (see
        ``ProviderTokenVerifier``), so this is the single place where an incoming
        request to the protected resource is authenticated.

        The token is a normal lab JWT, so this delegates to the same
        :class:`AuthorizationService` the REST routes use: it validates the JWT
        *and* sets the current user in the request context. That is why the code
        behind the resource (e.g. the MCP tools) needs no auth code of its own.

        Returning ``None`` makes the transport answer ``401`` with the
        ``WWW-Authenticate`` header a client needs to start the OAuth flow.
        """
        try:
            auth_context = AuthorizationService.authenticate_from_token(
                JWTService.AUTH_SCHEME + token
            )
        except Exception:
            # Malformed, expired, wrong secret, unknown or inactive user: all are
            # authentication failures. Do not leak which.
            Logger.debug("OAuth: rejected an invalid bearer token")
            return None

        user = auth_context.get_user()

        return AccessToken(
            token=token,
            client_id=user.id,
            scopes=[],
            subject=user.id,
            resource=self._resource_url,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        stored = self._refresh_tokens.get(refresh_token)
        if stored is None or stored.client_id != client.client_id:
            return None
        if stored.expires_at is not None and stored.expires_at < time.time():
            self._refresh_tokens.pop(refresh_token, None)
            return None
        return stored

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Issue a fresh lab JWT (and a fresh refresh token) from a refresh token.

        Without this, the 2-day lab JWT would force a browser re-login every two
        days; the OAuth spec (and the library's client registration) require refresh
        support. Both tokens are rotated, as the spec recommends.

        The user is re-checked at every refresh (in ``_mint_lab_token``), so access
        revoked in the lab takes effect on the next refresh rather than lingering
        for the life of a long-lived credential.
        """
        if refresh_token.subject is None:
            raise TokenError("invalid_grant", "Refresh token is not bound to a user.")

        # Rotate: the presented refresh token is single-use.
        self._refresh_tokens.pop(refresh_token.token, None)

        granted_scopes = scopes or refresh_token.scopes
        access_token = self._mint_lab_token(refresh_token.subject, granted_scopes)
        new_refresh = self._issue_refresh_token(
            client_id=refresh_token.client_id,
            user_id=refresh_token.subject,
            scopes=granted_scopes,
        )

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=JWTService.get_token_duration_in_seconds(),
            refresh_token=new_refresh,
            scope=" ".join(refresh_token.scopes) if refresh_token.scopes else None,
        )

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _mint_lab_token(user_id: str, scopes: list[str] | None = None) -> str:
        """Mint the lab access token for ``user_id``.

        Re-checks the user is still known and active at token time, then strips
        the ``Bearer `` prefix ``create_jwt`` adds: OAuth transports the bare
        token and the client re-adds the scheme.

        This is the **single place** a grant becomes a credential, and so the place
        scopes will be enforced. ``scopes`` is already threaded through every
        caller but deliberately ignored for now: the token is a full lab session
        (see the module warning). Binding it -- e.g. via ``create_app_jwt``-style
        claims, checked by ``AuthorizationService`` -- changes this method only.

        :param user_id: The user the token acts as.
        :param scopes: The scopes granted. Currently unenforced.
        """
        user = UserService.get_by_id_or_none(user_id)
        if user is None or not user.is_active:
            raise TokenError("invalid_grant", "User no longer has access to this lab.")

        token = JWTService.create_jwt(user_id)
        if token.startswith(JWTService.AUTH_SCHEME):
            token = token[len(JWTService.AUTH_SCHEME) :]
        return token

    def _issue_refresh_token(self, client_id: str, user_id: str, scopes: list[str]) -> str:
        """Mint and store a refresh token bound to a client and a lab user."""
        token = secrets.token_urlsafe(32)
        self._refresh_tokens[token] = RefreshToken(
            token=token,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(time.time() + REFRESH_TOKEN_TTL_SECONDS),
            subject=user_id,
        )
        return token

    def _forget_code(self, code: str) -> None:
        self._auth_codes.pop(code, None)
        self._code_user_ids.pop(code, None)

    def _prune_pending_logins(self) -> None:
        """Drop abandoned logins so the in-memory map cannot grow unbounded."""
        expired = [state for state, p in self._pending_logins.items() if p.is_expired()]
        for state in expired:
            del self._pending_logins[state]
