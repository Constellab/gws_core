import logging
import os
from abc import abstractmethod
from json import load
from typing import Any, cast
from urllib.parse import parse_qsl, urlencode

import reflex as rx
from typing_extensions import TypedDict

from .reflex_code_exchange import exchange_code_for_jwt, validate_jwt_for_user
from .reflex_exception import ReflexAppException

UNAUTHORIZED_ROUTE = "/unauthorized"
APP_CONFIG_FILENAME = "app_config.json"

# Standard-library logger: this module cannot import gws_core (it runs in virtual-env apps),
# so the GWS Logger is unavailable. Output lands in the app process stdout/stderr.
_logger = logging.getLogger(__name__)

# Name of the client-side cookie holding the session JWT so auth survives a page reload
# (F5 / new tab) on a standalone app link. This is an rx.Cookie (JS-readable, not HttpOnly):
# Reflex has no supported way to read an HttpOnly cookie from the websocket handshake, and its
# two-host front/back split makes the Streamlit-style nginx cookie impractical. The JWT is the
# same one already validated server-side and already held in client state. Mirrors
# AppGatewayService.APP_JWT_COOKIE_NAME (this module cannot import gws_core).
_APP_JWT_COOKIE_NAME = "gws_app_jwt"

# Cookie lifetime. Without max_age an rx.Cookie is a *session* cookie: the browser drops it when the
# tab/browser closes, so the app forgot the visitor long before the 2-day JWT expired — reading as
# "the app logs me out constantly". 30 days outlives the JWT on purpose: the JWT stays the real
# authority (validated, and re-minted while in use), the cookie is only its persistent store. An
# expired JWT in a still-present cookie is handled by _authenticate_from_jwt (clears + re-enters the
# gateway).
_APP_JWT_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30

# Core-api route that maps an app host back to its app key and redirects to the lab gateway (auth
# guard + cold-start + progress UI). Used to re-enter the gateway when the app holds no usable
# credential: a shared app URL whose single-use `gws_code` was already spent, or one carrying none at
# all. Reached directly on the lab API (GWS_LAB_API_URL) rather than through the app host, because
# the nginx fallback location only exists on the catch-all block -- a *running* app's own block would
# serve this path from the app itself.
# Mirrors app_gateway_constants.APP_FALLBACK_ENDPOINT_SEGMENT (this module cannot import gws_core).
_APP_FALLBACK_ENDPOINT = "apps/fallback/resolve"

# Marker added to the in-app path when bouncing to the gateway for a fresh code. Reflex state is
# cleared by the full page reload the bounce causes, so the "already tried" flag has to live in the
# URL. If the app comes back still unauthenticated *with* this marker, something is genuinely wrong
# (clock skew, revoked user, misconfigured app) and bouncing again would ping-pong the browser
# between app and gateway forever -- so the second failure surfaces as a plain error.
_GATEWAY_RETRY_QUERY_PARAM = "gws_gateway_retry"

# Second, independent home for that same marker. The query-param round-trip only survives if the
# front re-appends the forwarded `target` query to the app URL it navigates to -- and the handoff
# URL it is built from (ReflexProcess.build_handoff_url) carries only `gws_code`. A cookie survives
# the reload on its own, so a permanently failing exchange cannot ping-pong the visitor even if the
# marker is dropped from the URL.
# Deliberately very short-lived, and cleared as soon as a credential is obtained: a loop rounds in
# well under a minute, whereas a visitor who simply abandoned the login page must not be met with an
# error the next time they open the app. It is a backstop for the query param, not the primary guard.
_GATEWAY_RETRY_COOKIE_NAME = "gws_gateway_retry"
_GATEWAY_RETRY_COOKIE_MAX_AGE_SECONDS = 60

# Query-param carrying the single-use handoff code in the app URL.
# Mirrors app_gateway_constants.GWS_CODE_QUERY_PARAM (this module cannot import gws_core).
_GWS_CODE_QUERY_PARAM = "gws_code"


class ReflexConfigDTO(TypedDict):
    source_ids: list[str]
    params: dict | None
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: dict[str, str]


class QueryParamObject:
    def __init__(self, query_param_str: str):
        """Initialize the QueryParamObject with a query parameter string."""
        self.query_param_str = query_param_str
        self.params = self._parse_query_params()

    def _parse_query_params(self) -> dict[str, str]:
        """Parse the query parameter string into a dictionary."""
        params = {}
        if self.query_param_str:
            for param in self.query_param_str.split("&"):
                key, value = param.split("=", 1)
                params[key] = value
        return params

    def get(self, key: str, default=None) -> str | None:
        """Get a parameter value by key."""
        return self.params.get(key, default)


class ReflexMainStateBase(rx.State, mixin=True):
    """Base State of Reflex. This state is used by normal app and virtual environment app.

    It is used to manage the app configuration, authentication, and parameters.
    """

    _app_config: dict | None = None
    _is_initialized: bool = False
    main_component_initialized: bool = False

    # None if the user is not authenticated
    authenticated_user_id: str | None = None

    user_access_token: str | None = None

    # Persistent copy of the session JWT, synced to a client-side cookie by Reflex so it survives
    # a page reload (state is otherwise cleared on refresh). Rehydrated automatically on load; the
    # F5-survival path in _check_user_token re-validates it. Written on a successful code exchange.
    jwt_cookie: str = rx.Cookie(
        name=_APP_JWT_COOKIE_NAME, same_site="lax", max_age=_APP_JWT_COOKIE_MAX_AGE_SECONDS
    )

    # Set just before bouncing to the gateway, cleared as soon as a credential is obtained. Backs the
    # loop guard together with the retry query param — see _GATEWAY_RETRY_COOKIE_NAME.
    gateway_retry_cookie: str = rx.Cookie(
        name=_GATEWAY_RETRY_COOKIE_NAME,
        same_site="lax",
        max_age=_GATEWAY_RETRY_COOKIE_MAX_AGE_SECONDS,
    )

    # Constant for dev mode
    DEV_MODE_USER_ACCESS_TOKEN_KEY = "dev_mode_token"
    DEV_MODE_APP_ID = "dev-app"
    # Sentinel app id baked into the compiled bundle during `reflex export` (build mode).
    # Frontend builds are shared across app instances, so the real app id must never be
    # compiled in — it is provided at runtime by the per-instance backend on hydration.
    BUILD_MODE_APP_ID = "gws-build"
    # Fixed token always provisioned for the system user by the launch side. Mirrors
    # AppProcess.SYSTEM_USER_ACCESS_TOKEN_KEY (this module cannot import gws_core, so the
    # literal is duplicated). Used by components opting into fallback_to_system_user.
    SYSTEM_USER_ACCESS_TOKEN_KEY = "system_user_token"

    MAIN_STATE_CLASS = type["ReflexMainStateBase"]

    @rx.event
    async def on_main_component_mount(self) -> "rx.event.EventSpec | None":
        """
        Event handler for when the main component is mounted.

        Use a specific method and a variable because the _is_initialized is
        set from a call that does not refresh the state.

        This is the only frame Reflex inspects the return value of, so anything ``_on_load``
        produces (currently the gateway redirect) MUST be returned from here. ``rx.redirect``
        only builds an ``EventSpec`` describing the navigation -- dropping it means the browser
        is never told to navigate and the app silently stays on an unauthenticated page.

        :return: the ``EventSpec`` produced by ``_on_load``, or None when nothing has to be
            executed client-side.
        :rtype: rx.event.EventSpec | None
        """
        redirect = await self._on_load()
        if redirect is not None:
            # The page is navigating away: do not flip main_component_initialized, otherwise
            # the app content renders to an unauthenticated visitor until the browser leaves.
            return redirect

        if not self._is_initialized:
            # _on_load bailed out before checking anything (router not ready yet). Leaving the
            # component uninitialized keeps the loader on screen until a later event retries;
            # flipping the flag here would render the app content to a visitor whose credential
            # was never checked.
            return None

        self.main_component_initialized = True
        return None

    async def _on_load(self) -> "rx.event.EventSpec | None":
        """Load the main state of the app. It initializes the app configuration and checks authentication.
        If the app requires authentication and the user is not authenticated,
        it returns a redirect to the lab gateway.

        To avoid circular dependency, this method should not call the `get_app_config` method.

        :return: an ``EventSpec`` redirecting to the gateway when the visitor holds no usable
            credential, otherwise None. The caller (``on_main_component_mount``) must return it
            to Reflex -- an ``EventSpec`` that is not returned is never executed.
        :rtype: rx.event.EventSpec | None
        """

        if self._is_initialized:
            # If already initialized, do nothing
            return None

        # the router might not be ready on first request so we skip until next call
        # otherwise we cannot get query params
        if not self._app_router_ready():
            # No retry is scheduled here: the caller keeps the component uninitialized so the next
            # event that reaches _on_load runs the checks. Logged because a visitor stuck on the
            # loader with no further event would otherwise be invisible.
            _logger.warning(
                "[gws-auth] _on_load: router not ready (url path is empty), skipping "
                "initialization until the next call."
            )
            return None

        authenticated_user_id = await self._load_and_check_user_authentication(store_in_state=True)

        requires_authentication = self.requires_authentication()

        if requires_authentication and not authenticated_user_id:
            # No usable credential: either a bare app URL (someone shared the address bar copy, whose
            # gws_code was scrubbed after the first open), a spent single-use code, or an expired JWT.
            # None of these is a dead end -- re-enter the gateway, which authenticates the visitor
            # (using their lab session when they have one) and hands back a fresh code.
            return self._redirect_to_gateway()

        # A credential was obtained (or none is required): release the loop guard so a later
        # bounce -- expired JWT, spent code on a shared link -- is not mistaken for a loop.
        if self.gateway_retry_cookie:
            self.gateway_retry_cookie = ""

        self._is_initialized = True

        await self._on_initialized()

        return None

    async def _load_and_check_user_authentication(self, store_in_state: bool = False) -> str | None:
        """Load the app configuration and check user authentication.

        This method can be called from both initialization flow and @rx.var contexts.
        It loads the app config if needed and checks user authentication without
        modifying the state unless explicitly requested.

        Args:
            store_in_state (bool): If True, stores the authenticated user ID in self.authenticated_user_id.
                                   If False, only returns the user ID without storing it (useful for @rx.var contexts).
                                   Defaults to False.

        Returns:
            str | None: The authenticated user ID if authentication succeeds, None otherwise.
        """
        # Load app config if not already loaded
        app_config = self._load_app_config(store_in_state=store_in_state)

        if self.authenticated_user_id:
            return self.authenticated_user_id

        # Check if router is ready (needed to get query params)
        if not self._app_router_ready():
            return None

        user_access_tokens = app_config.get("user_access_tokens", {})
        # Only the initialization path (store_in_state=True, i.e. _on_load) may consume the
        # single-use gws_code. @rx.var / read-only contexts (store_in_state=False) run
        # concurrently and repeatedly on a load — letting them exchange too would re-submit the
        # already-consumed code (403 "Invalid url"). They only validate an existing JWT.
        user_id = await self._check_user_token(user_access_tokens, allow_code_exchange=store_in_state)

        # Store in state if requested
        if store_in_state and user_id:
            self.authenticated_user_id = user_id

        return user_id

    @abstractmethod
    async def _on_initialized(self) -> None:
        """Called when the base state has finished initialization.

        Override this method in subclasses to perform actions after initialization.
        """
        pass

    def _load_app_config(self, store_in_state: bool = False) -> dict:
        """Load the app configuration from the environment variable."""
        if self._app_config is not None:
            return self._app_config

        app_config_path = self._get_app_config_file_path()

        if not app_config_path:
            return {}

        if not os.path.exists(app_config_path):
            # Logger.warning(f"App config file not found at {app_config_path}")
            # return {}
            raise ReflexAppException(f"App config file not found at {app_config_path}")

        try:
            app_config: dict
            with open(app_config_path, encoding="utf-8") as file:
                app_config = load(file)

            if store_in_state:
                self._app_config = app_config
            return app_config

        except Exception as e:
            raise ReflexAppException(f"Error reading app config file: {e}")

    def _get_app_config_file_path(self) -> str:
        config_file_path = os.environ.get("GWS_APP_CONFIG_FILE_PATH")
        if not config_file_path:
            raise ReflexAppException(
                "GWS_APP_CONFIG_FILE_PATH environment variable is not set in production mode"
            )

        return config_file_path

    def get_app_id(self) -> str:
        """Get the app ID from the environment variable."""
        if self.is_build_mode():
            # never bake the builder instance's app id into the shared bundle
            return self.BUILD_MODE_APP_ID

        if self.is_dev_mode():
            return self.DEV_MODE_APP_ID

        app_id = os.environ.get("GWS_APP_ID")
        if not app_id:
            raise ReflexAppException("GWS_APP_ID environment variable is not set")
        return app_id

    async def _check_user_token(
        self, user_access_tokens: dict[str, str], allow_code_exchange: bool = False
    ) -> str | None:
        # A PUBLIC app never authenticates a user, even in dev mode, so it simulates a
        # public prod app.
        if not self.requires_authentication():
            return None

        # Dev mode: authenticate via the fixed dev sentinel token stored in the app config
        # (no gws_code / cookie flow in dev).
        if self.is_dev_mode():
            return user_access_tokens.get(self.DEV_MODE_USER_ACCESS_TOKEN_KEY)

        # Prod: a single-use gws_code is exchanged once for a JWT that then persists (state +
        # client cookie). The JWT is checked FIRST: the code is destructive (single-use), and this
        # method runs several times per load (router-ready retry, and each bound @rx.var).
        # Re-submitting a spent code would 403; validating the already obtained JWT is idempotent,
        # so it must win whenever a JWT is available.
        user_id = self._authenticate_from_jwt()
        if user_id is not None:
            return user_id

        # First open: exchange the one-time gws_code from the URL (stores the JWT in state +
        # cookie for subsequent runs and reloads). Guarded to the initialization path only —
        # concurrent @rx.var contexts must not race to consume the same single-use code.
        if allow_code_exchange:
            return self._exchange_code_if_present()

        return None

    def _exchange_code_if_present(self) -> str | None:
        """If a single-use gws_code is in the URL, exchange it for a JWT and return the user id.

        On success, stores the JWT as the user access token (carried on later API calls) and
        removes gws_code from the browser URL so nothing reusable lingers. Returns None when no
        code is present (caller falls through to the legacy token path).

        A gws_code that is present but cannot be exchanged is **not** an error: the code is
        single-use, so this is exactly what a *shared* app URL looks like once the first visitor
        consumed it (or after a reload replayed a spent one). Returning None lets the caller
        re-enter the gateway for a fresh code instead of dead-ending the visitor.
        """
        query_params = self.get_query_params()
        code = query_params.get(_GWS_CODE_QUERY_PARAM)
        if not code:
            return None

        exchanged = exchange_code_for_jwt(self.get_app_id(), code)
        if exchanged is None:
            # spent/expired code (typically a shared URL): drop it and let the caller re-enter the
            # gateway, which mints a new one. Scrub it first so a retry cannot replay it.
            self._scrub_gws_code_from_url()
            return None

        # the JWT becomes the user access token the app carries to the data lab API
        self.user_access_token = exchanged.user_access_token
        # persist it in the client cookie so auth survives a page reload (F5 / new tab)
        self.jwt_cookie = exchanged.user_access_token
        # scrub gws_code from the URL (single-use; keep it out of history/referrers)
        self._scrub_gws_code_from_url()
        return exchanged.user_id

    def _authenticate_from_jwt(self) -> str | None:
        """Try to authenticate from the session JWT, returning the user id.

        The JWT lives in jwt_cookie — the authoritative, persistent store: it is written on a
        successful code exchange and rehydrated by Reflex from the client cookie on a page reload
        (F5 / new tab). It is kept separate from user_access_token, which may instead hold the
        *legacy* opaque access token (gws_user_access_token) that is NOT a JWT and would fail
        validation. Validating a JWT is idempotent, so this path is safe to run repeatedly and
        wins over re-exchanging a single-use code. The app cannot validate the JWT itself (no
        gws_core / no secret), so it relays it to the lab. Returns None when there is no JWT or it
        is invalid/expired.
        """
        jwt = self.jwt_cookie
        if not jwt:
            return None

        validated = validate_jwt_for_user(self.get_app_id(), jwt)
        if validated is None:
            # stale/expired JWT: clear it so it is not retried on every run/reload
            self.jwt_cookie = ""
            return None

        # The lab re-mints the token once it is half-expired, so an app in active use keeps a
        # rolling session rather than being cut off a fixed 2 days after the handoff.
        if validated.renewed_jwt:
            jwt = validated.renewed_jwt
            self.jwt_cookie = jwt

        # the validated JWT is also the token the app carries on later data lab API calls
        self.user_access_token = jwt
        return validated.user_id

    def _redirect_to_gateway(self) -> "rx.event.EventSpec":
        """Send the browser to the lab's fallback resolver, which re-enters the gateway.

        The resolver maps this app's host back to its app key and redirects to the gateway, so the
        visitor is authenticated (transparently when they hold a lab session) and comes back with a
        fresh single-use code. The current in-app path is forwarded as ``target`` so a shared deep
        link still lands where it pointed.

        In dev mode there is no gateway, so this stays an exception: a dev app failing auth is a
        configuration problem the developer should see, not something to bounce.

        :raises ReflexAppException: when bouncing is impossible (dev mode, unknown gateway address,
            no host) or when the visitor already came back from the gateway unauthenticated.
        :return: the ``EventSpec`` navigating the browser to the gateway. The caller must return it
            to Reflex -- an ``EventSpec`` that is not returned is never executed.
        :rtype: rx.event.EventSpec
        """
        lab_api_url = (os.environ.get("GWS_LAB_API_URL") or "").rstrip("/")
        if self.is_dev_mode():
            _logger.warning(
                "[gws-auth] Not redirecting to the lab login: the app runs in dev mode "
                "(GWS_IS_DEV_MODE=true), where there is no gateway. Authentication in dev "
                "comes from the '%s' entry of the app config file.",
                self.DEV_MODE_USER_ACCESS_TOKEN_KEY,
            )
            raise ReflexAppException("User not authenticated")

        if not lab_api_url:
            _logger.warning(
                "[gws-auth] Not redirecting to the lab login: GWS_LAB_API_URL is not set in the "
                "app environment, so the gateway address is unknown."
            )
            raise ReflexAppException("User not authenticated")

        host = self._resolve_request_host()
        if not host:
            # without a host the resolver cannot identify the app; surface the plain failure
            _logger.warning(
                "[gws-auth] Not redirecting to the lab login: the request carries no host "
                "(neither router.url.netloc nor a Host header), so the resolver cannot map it "
                "back to an app key."
            )
            raise ReflexAppException("User not authenticated")

        query_params = self.get_query_params()
        # Either home of the marker is enough: the query param is dropped whenever the front does not
        # carry the forwarded target's query over to the app URL, the cookie whenever it expired or
        # the browser refuses it.
        if query_params.get(_GATEWAY_RETRY_QUERY_PARAM) or self.gateway_retry_cookie:
            # already came back from the gateway and still no credential: stop, do not loop
            _logger.warning(
                "[gws-auth] Came back from the lab gateway still unauthenticated (app '%s', "
                "host '%s'). Not bouncing again to avoid a redirect loop. Likely causes: the "
                "app key is not registered for this host, the user was revoked, or clock skew "
                "invalidates the minted code.",
                self.get_app_id(),
                host,
            )
            raise ReflexAppException("User not authenticated")

        path = self.router.url.path or "/"

        # Drop any gws_code still on the URL: it is the spent one that sent us here (the scrub in
        # _exchange_code_if_present is a client-side history rewrite, so the server-side router still
        # sees it). Carrying it would put a stale code next to the fresh one the gateway appends.
        kept_params = [
            (key, value)
            for key, value in parse_qsl(self.router.url.query or "")
            if key not in (_GWS_CODE_QUERY_PARAM, _GATEWAY_RETRY_QUERY_PARAM)
        ]
        # mark the target so a second failure is detected instead of bouncing again
        kept_params.append((_GATEWAY_RETRY_QUERY_PARAM, "1"))
        target = f"{path}?{urlencode(kept_params)}"

        params = urlencode({"host": host, "target": target})
        redirect_url = f"{lab_api_url}/core-api/{_APP_FALLBACK_ENDPOINT}?{params}"
        _logger.debug(
            "[gws-auth] No usable credential for app '%s'; redirecting to the lab gateway: %s",
            self.get_app_id(),
            redirect_url,
        )
        # Remember the bounce client-side: the reload wipes Reflex state, so this is the only part of
        # the guard that does not depend on the URL surviving the gateway round-trip.
        self.gateway_retry_cookie = "1"
        return rx.redirect(redirect_url)

    def _resolve_request_host(self) -> str:
        """Return the app's own host (``host[:port]``), or "" if it cannot be determined.

        Sending the port is fine: the fallback resolver strips it when mapping the host back to
        an app key.

        ``router.url.netloc`` is the preferred source: Reflex builds ``router.url`` by concatenating
        the ``origin`` *header* with the page path (``RouterData.from_router_data``), and the browser
        always sends ``Origin`` on the websocket handshake the router data comes from. The ``Host``
        header is the fallback for the case where it does not (a non-browser client, a proxy that
        strips it): it is mandatory on every HTTP/1.1 request and is what nginx already routes on.
        """
        netloc = self.router.url.netloc or ""
        if netloc:
            return netloc

        return self.router.headers.host or ""

    def _scrub_gws_code_from_url(self) -> None:
        """Remove the gws_code query param from the browser URL via a history replace."""
        rx.call_script(
            "if (window.history && window.location.search.includes('gws_code')) {"
            " const u = new URL(window.location.href);"
            " u.searchParams.delete('gws_code');"
            " window.history.replaceState({}, '', u.toString()); }"
        )

    async def get_app_config(self) -> ReflexConfigDTO:
        """Get the app configuration."""
        if self._app_config is None:
            return cast(ReflexConfigDTO, self._load_app_config(store_in_state=False))
        # raise ValueError("App configuration is not loaded. Call on_load() first.")
        return cast(ReflexConfigDTO, self._app_config)

    async def get_sources_ids(self) -> list[str]:
        """Get the source IDs from the app configuration."""
        app_config = await self.get_app_config()
        source_ids = app_config.get("source_ids")
        if source_ids is None:
            return []
        return source_ids

    def is_virtual_env_app(self) -> bool:
        """Check if the app is running in a virtual environment."""
        return os.environ.get("GWS_IS_VIRTUAL_ENV", "false").lower() == "true"

    def _app_router_ready(self) -> bool:
        return self.router.url.path is not None and self.router.url.path != ""

    def get_query_params(self) -> QueryParamObject:
        """Get the query parameters from the app configuration."""
        return QueryParamObject(self.router.url.query)

    ##################### AUTHENTICATION #####################

    def get_access_mode(self) -> str:
        """Return the app access mode (AUTHENTICATED / PUBLIC).

        Read as a plain string from the GWS_APP_ACCESS_MODE env var so gws_reflex_base
        stays free of any gws_core import (it runs in virtual env apps without gws_core).
        Defaults to AUTHENTICATED.
        """
        return os.environ.get("GWS_APP_ACCESS_MODE", "AUTHENTICATED")

    def requires_authentication(self) -> bool:
        """Check if the app requires authentication (AUTHENTICATED access mode)."""
        return self.get_access_mode() == "AUTHENTICATED"

    async def check_authentication(self) -> bool:
        """Check if the current user is authenticated.

        This method is safe to call from @rx.var contexts as it does not modify state
        when called before initialization. It will load and check authentication without
        storing the result in the state.

        Returns:
            bool: True if the user is authenticated (or if authentication is not required),
                  False otherwise.
        """
        if not self.requires_authentication():
            return True
        # NOTE: this legitimately returns False during a normal load -- computed vars are
        # evaluated on hydration, concurrently with (and often before) _on_load completes the
        # code exchange, so there is no user yet and the vars recompute once init finishes.
        user_id = await self._load_and_check_user_authentication(store_in_state=False)
        return user_id is not None

    def _get_user_access_token(self) -> str | None:
        """Return the token the app carries on data lab API calls for the current user.

        In dev mode this is the fixed dev sentinel token; in prod it is the session JWT obtained
        from the gws_code exchange (or the cookie on reload), stored in self.user_access_token by
        the authentication flow.
        """
        if self.is_dev_mode():
            return self.DEV_MODE_USER_ACCESS_TOKEN_KEY

        return self.user_access_token

    async def _get_system_user_access_token(self) -> str | None:
        """Return the access token of the system user, if the launch side provisioned one.

        The token is provisioned for every non-dev app (stored in the app config but never
        in the URL). It lets front components fall back to running their API requests as the
        system user. Returns None if it is not available (e.g. a dev-mode app).
        """
        app_config = await self.get_app_config()
        user_access_tokens = app_config.get("user_access_tokens") or {}
        if self.SYSTEM_USER_ACCESS_TOKEN_KEY in user_access_tokens:
            return self.SYSTEM_USER_ACCESS_TOKEN_KEY
        return None

    ####################### PARAMS #####################

    async def get_param(self, key: str, default=None) -> Any | None:
        """Get a parameter from the app configuration."""
        params = await self.get_params()
        return params.get(key, default)

    async def get_params(self) -> dict:
        """Get the parameters from the app configuration."""
        app_config = await self.get_app_config()
        params = app_config.get("params")
        if params is None:
            return {}
        return params

    ###################### UTILITIES #####################
    @classmethod
    def is_dev_mode(cls) -> bool:
        """Check if the app is running in development mode."""
        return os.environ.get("GWS_IS_DEV_MODE", "false").lower() == "true"

    @classmethod
    def is_build_mode(cls) -> bool:
        """True while the frontend is being compiled (`reflex export`).

        Set by gws_core's ReflexProcess in the export env. State code evaluated at
        compile time (e.g. `@rx.var` initial values) must bake neutral values in this
        mode: the bundle is shared across app instances, so nothing instance-specific
        may end up in it. Real values arrive at runtime on websocket hydration.
        """
        return os.environ.get("GWS_REFLEX_BUILD_MODE") == "1"

    async def get_first_child_of_state(self, state_class: type[rx.State]) -> rx.State | None:
        """Get the first child state of a given type.

        Args:
            state_class (type): The class of the state to find.

        Returns:
            Optional[rx.State]: The first child state of the given type, or None if not found.
        """
        root_state = self.get_root_state()
        sub_states = root_state.get_substates()

        for sub in sub_states:
            if issubclass(sub, state_class):
                return await self.get_state(sub)

        return None


class ReflexMainStateBaseFactory:
    """Class to store the main state class to use because the
    ReflexMainStateBase is an abstract class and cannot be instantiated directly.
    So in the gws_reflex_base package we must use this factory to get the main state class.

    And this is set in the gws_reflex_main or gws_reflex_env package when registering the app.

    """

    __MAIN_STATE_CLASS__: type[ReflexMainStateBase] | None = None

    @staticmethod
    def set_main_state_class(main_state_class: type[ReflexMainStateBase]) -> None:
        """Set the main state class to use for the Reflex app.

        Args:
            main_state_class (type): The main state class to set.
        """
        ReflexMainStateBaseFactory.__MAIN_STATE_CLASS__ = main_state_class

    @staticmethod
    def get_main_state_class() -> type[ReflexMainStateBase]:
        """Get the main state class to use for the Reflex app.

        Returns:
            type: The main state class.
        """
        if ReflexMainStateBaseFactory.__MAIN_STATE_CLASS__ is None:
            raise ValueError("Main state class is not set. Call set_main_state_class() first.")
        return ReflexMainStateBaseFactory.__MAIN_STATE_CLASS__
