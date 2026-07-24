"""OAuth authorization server for the lab's MCP endpoint.

Why the lab issues its own tokens
---------------------------------
The MCP tools run **inside the lab** against the lab's databases, so they need a
**lab JWT** -- the token :class:`JWTService` signs with the lab's ``secret_key``
and every lab route already validates. The Constellab community token obtained by
``gws community login`` is a *different* token from a *different* issuer
(``api.constellab.community``); the lab would reject it.

So Constellab is used for the **identity** step (prove, in a browser, who you
are), and the lab mints the **resource token** for MCP. This is the standard
shape the MCP SDK documents as the "3rd Party OAuth" flow::

    +--------+     +------------+     +-------------------+
    | Claude | --> | MCP Server | --> | Constellab        |
    | (local)|     | (the lab)  |     | (identity)        |
    +--------+     +------------+     +-------------------+

What we implement vs. what the SDK does
---------------------------------------
The SDK's ``create_auth_routes`` serves the whole OAuth surface -- discovery
documents, ``/register`` (DCR), ``/authorize``, ``/token``, PKCE verification and
redirect_uri validation -- driven by the provider below. This class only supplies
the Constellab-specific behaviour:

- ``authorize``    -> start the Constellab device-code login, return its URL
- the callback     -> exchange the device code, map the identity to a lab user,
                      mint an authorization code, redirect back to the client
- ``exchange_*``   -> mint the lab JWT as the OAuth access token

State (clients, pending logins, codes) is kept **in memory**: it is short-lived
and a lab restart simply forces a re-login.
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
from gws_core.mcp.mcp_constellab_login import ConstellabLoginService
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


@dataclass
class _PendingLogin:
    """A browser login started by /authorize and not yet completed by the callback."""

    device_code: str
    params: AuthorizationParams
    client_id: str
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        return time.time() - self.created_at > PENDING_LOGIN_TTL_SECONDS


class ConstellabOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """Authorization server bridging MCP clients to Constellab identity.

    :param callback_url: Absolute URL of the lab route that finishes the
        Constellab leg of the flow (see ``mcp_controller``).
    :param resource_url: The canonical MCP resource URL, echoed back on issued
        access tokens as the RFC 8707 resource indicator.
    """

    def __init__(self, callback_url: str, resource_url: str) -> None:
        self._callback_url = callback_url
        self._resource_url = resource_url

        self._clients: dict[str, OAuthClientInformationFull] = {}
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
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info
        Logger.debug(f"MCP OAuth: registered client '{client_info.client_id}'")

    # ------------------------------------------------------------------ #
    #  Authorization: hand the user off to Constellab
    # ------------------------------------------------------------------ #

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Start a Constellab browser login and return the URL to redirect to.

        The MCP client's OAuth parameters (PKCE challenge, redirect_uri, state)
        are stashed against an opaque ``login_state`` so the callback can finish
        the flow. The SDK verifies the PKCE challenge later, at /token.
        """
        device_code, auth_url = ConstellabLoginService.request_device_code()

        login_state = secrets.token_urlsafe(32)
        self._pending_logins[login_state] = _PendingLogin(
            device_code=device_code,
            params=params,
            client_id=client.client_id,
        )
        self._prune_pending_logins()

        # Constellab redirects/returns to our callback, which carries login_state
        # so we can recover the MCP client's request.
        return construct_redirect_uri(
            self._callback_url,
            constellab_auth_url=auth_url,
            login_state=login_state,
        )

    def complete_authorization(self, login_state: str, user: User) -> str:
        """Finish the flow for ``login_state``: mint a code, return the client redirect.

        Called by the callback route once the Constellab identity has been
        resolved to a lab :class:`User`.

        :param login_state: The opaque state issued by :meth:`authorize`.
        :param user: The authenticated lab user.
        :return: The URL to redirect the MCP client back to.
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

        access_token = self._mint_lab_jwt(user_id)
        refresh_token = self._issue_refresh_token(
            client_id=client.client_id,
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
        """Verify a bearer token presented on an MCP call.

        The SDK derives its token verifier from this method (see
        ``ProviderTokenVerifier``), so this is the single place where an incoming
        MCP request is authenticated.

        The token is a normal lab JWT, so this delegates to the same
        :class:`AuthorizationService` the REST routes use: it validates the JWT
        *and* sets the current user in the request context. That is why the tools
        in ``db_mcp`` need no auth code of their own.

        Returning ``None`` makes the MCP layer answer ``401`` with the
        ``WWW-Authenticate`` header an MCP client needs to start the OAuth flow.
        """
        try:
            auth_context = AuthorizationService.authenticate_from_token(
                JWTService.AUTH_SCHEME + token
            )
        except Exception:
            # Malformed, expired, wrong secret, unknown or inactive user: all are
            # authentication failures. Do not leak which.
            Logger.debug("MCP: rejected an invalid bearer token")
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
        days; the MCP spec (and the SDK's client registration) require refresh
        support. Both tokens are rotated, as the spec recommends.

        The user is re-checked at every refresh (in ``_mint_lab_jwt``), so access
        revoked in the lab takes effect on the next refresh rather than lingering
        for the life of a long-lived credential.
        """
        if refresh_token.subject is None:
            raise TokenError("invalid_grant", "Refresh token is not bound to a user.")

        # Rotate: the presented refresh token is single-use.
        self._refresh_tokens.pop(refresh_token.token, None)

        access_token = self._mint_lab_jwt(refresh_token.subject)
        new_refresh = self._issue_refresh_token(
            client_id=refresh_token.client_id,
            user_id=refresh_token.subject,
            scopes=scopes or refresh_token.scopes,
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
    def _mint_lab_jwt(user_id: str) -> str:
        """Mint the lab access token for ``user_id``.

        Re-checks the user is still known and active at token time, then strips
        the ``Bearer `` prefix ``create_jwt`` adds: OAuth transports the bare
        token and the client re-adds the scheme.
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
