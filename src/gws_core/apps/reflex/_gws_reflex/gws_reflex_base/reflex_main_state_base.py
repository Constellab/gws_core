import os
from abc import abstractmethod
from json import load
from typing import Any, cast

import reflex as rx
from typing_extensions import TypedDict

UNAUTHORIZED_ROUTE = "/unauthorized"
APP_CONFIG_FILENAME = "app_config.json"


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

    _app_config: dict = None
    _is_initialized: bool = False
    main_component_initialized: bool = False

    # None if the user is not authenticated
    authenticated_user_id: str | None = None

    user_access_token: str | None = None

    # Constant for dev mode
    DEV_MODE_USER_ACCESS_TOKEN_KEY = "dev_mode_token"
    DEV_MODE_APP_ID = "dev-app"

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
            raise Exception("User not authenticated")
            return rx.redirect(UNAUTHORIZED_ROUTE)

        self._is_initialized = True
        print("ReflexMainStateBase initialized")

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
        if not self._app_config:
            _app_config = self._load_app_config()
            if store_in_state:
                self._app_config = _app_config
        else:
            _app_config = self._app_config

        if self.authenticated_user_id:
            return self.authenticated_user_id

        # Check if router is ready (needed to get query params)
        if not self._app_router_ready():
            return None

        user_access_tokens = _app_config.get("user_access_tokens", {})
        user_id = await self._check_user_token(user_access_tokens)

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

    def _load_app_config(self) -> dict:
        """Load the app configuration from the environment variable."""
        app_config_path = self._get_app_config_file_path()

        if not app_config_path:
            return {}

        if not os.path.exists(app_config_path):
            # Logger.warning(f"App config file not found at {app_config_path}")
            # return {}
            raise FileNotFoundError(f"App config file not found at {app_config_path}")

        try:
            with open(app_config_path, encoding="utf-8") as file:
                return load(file)

        except Exception as e:
            raise ValueError(f"Error reading app config file: {e}")

    def _get_app_config_file_path(self) -> str:
        config_file_path = os.environ.get("GWS_APP_CONFIG_FILE_PATH")
        if not config_file_path:
            raise ValueError(
                "GWS_APP_CONFIG_FILE_PATH environment variable is not set in production mode"
            )

        return config_file_path

    def get_app_id(self) -> str:
        """Get the app ID from the environment variable."""
        if self.is_dev_mode():
            return self.DEV_MODE_APP_ID

        app_id = os.environ.get("GWS_APP_ID")
        if not app_id:
            raise ValueError("GWS_APP_ID environment variable is not set")
        return app_id

    async def _check_user_token(self, user_access_tokens: dict[str, str]) -> str | None:
        if not self.is_dev_mode():
            query_params = self.get_query_params()

            url_token = query_params.get("gws_token")

            env_token = os.environ.get("GWS_APP_TOKEN")

            if url_token != env_token:
                return None

        # load user id from access token
        user_access_token = self._get_user_access_token()
        if user_access_token is None:
            return None

        return user_access_tokens.get(user_access_token)

    async def get_app_config(self) -> ReflexConfigDTO:
        """Get the app configuration."""
        if self._app_config is None:
            await self._on_load()
        # raise ValueError("App configuration is not loaded. Call on_load() first.")
        return cast(ReflexConfigDTO, self._app_config)

    async def get_sources_ids(self) -> list[str]:
        """Get the source IDs from the app configuration."""
        source_ids = (await self.get_app_config()).get("source_ids")
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

    def requires_authentication(self) -> bool:
        """Check if the app requires authentication."""
        return os.environ.get("GWS_REQUIRES_AUTHENTICATION", "true").lower() == "true"

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
        """Get the user access token from the app configuration."""
        if self.is_dev_mode():
            return self.DEV_MODE_USER_ACCESS_TOKEN_KEY

        if not self.user_access_token:
            query_params = self.get_query_params()
            self.user_access_token = query_params.get("gws_user_access_token")
        return self.user_access_token

    ####################### PARAMS #####################

    async def get_param(self, key: str, default=None) -> Any | None:
        """Get a parameter from the app configuration."""
        params = await self.get_params()
        return params.get(key, default)

    async def get_params(self) -> dict:
        """Get the parameters from the app configuration."""
        params = (await self.get_app_config()).get("params")
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
