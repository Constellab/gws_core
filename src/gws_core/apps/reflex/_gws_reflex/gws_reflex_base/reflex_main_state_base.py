import os
from abc import abstractmethod
from json import load
from typing import Any, cast

import reflex as rx
from typing_extensions import TypedDict

from .reflex_code_exchange import exchange_code_for_jwt, validate_jwt_for_user
from .reflex_exception import ReflexAppException

UNAUTHORIZED_ROUTE = "/unauthorized"
APP_CONFIG_FILENAME = "app_config.json"

# Name of the client-side cookie holding the session JWT so auth survives a page reload
# (F5 / new tab) on a standalone app link. This is an rx.Cookie (JS-readable, not HttpOnly):
# Reflex has no supported way to read an HttpOnly cookie from the websocket handshake, and its
# two-host front/back split makes the Streamlit-style nginx cookie impractical. The JWT is the
# same one already validated server-side and already held in client state. Mirrors
# AppGatewayService.APP_JWT_COOKIE_NAME (this module cannot import gws_core).
_APP_JWT_COOKIE_NAME = "gws_app_jwt"


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
    jwt_cookie: str = rx.Cookie(name=_APP_JWT_COOKIE_NAME, same_site="lax")

    # Constant for dev mode
    DEV_MODE_USER_ACCESS_TOKEN_KEY = "dev_mode_token"
    DEV_MODE_APP_ID = "dev-app"
    # Fixed token always provisioned for the system user by the launch side. Mirrors
    # AppProcess.SYSTEM_USER_ACCESS_TOKEN_KEY (this module cannot import gws_core, so the
    # literal is duplicated). Used by components opting into fallback_to_system_user.
    SYSTEM_USER_ACCESS_TOKEN_KEY = "system_user_token"

    MAIN_STATE_CLASS = type["ReflexMainStateBase"]

    @rx.event
    async def on_main_component_mount(self):
        """
        Event handler for when the main component is mounted.

        Use a specific method and a variable because the _is_initialized is
        set from a call that does not refresh the state.
        """
        await self._on_load()
        self.main_component_initialized = True

    async def _on_load(self):
        """Load the main state of the app. It initializes the app configuration and checks authentication.
        If the app requires authentication and the user is not authenticated,
        it redirects to the unauthorized page.

        To avoid circular dependency, this method should not call the `get_app_config` method.

        :return: _description_
        :rtype: _type_
        """

        if self._is_initialized:
            # If already initialized, do nothing
            return

        # the router might not be ready on first request so we skip until next call
        # otherwise we cannot get query params
        if not self._app_router_ready():
            return

        authenticated_user_id = await self._load_and_check_user_authentication(store_in_state=True)

        requires_authentication = self.requires_authentication()

        if requires_authentication and not authenticated_user_id:
            # If the app requires authentication and the user is not authenticated,
            # redirect to the unauthorized page
            raise ReflexAppException("User not authenticated")
            return rx.redirect(UNAUTHORIZED_ROUTE)

        self._is_initialized = True

        await self._on_initialized()

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

        Raises ReflexAppException when a gws_code IS present but cannot be exchanged: it is
        single-use and short-lived, so this means the link was already opened or expired. Raising
        here surfaces an accurate message instead of degrading into the generic
        "User not authenticated".
        """
        query_params = self.get_query_params()
        code = query_params.get("gws_code")
        if not code:
            return None

        exchanged = exchange_code_for_jwt(self.get_app_id(), code)
        if exchanged is None:
            raise ReflexAppException(
                "This app link has expired or was already used. "
                "Please reopen the app to get a fresh link."
            )

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

        user_id = validate_jwt_for_user(self.get_app_id(), jwt)
        if user_id is None:
            # stale/expired JWT: clear it so it is not retried on every run/reload
            self.jwt_cookie = ""
            return None

        # the validated JWT is also the token the app carries on later data lab API calls
        self.user_access_token = jwt
        return user_id

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
