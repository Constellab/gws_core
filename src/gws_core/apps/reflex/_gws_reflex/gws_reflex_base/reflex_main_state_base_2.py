import os
from asyncio import sleep
from json import load
from typing import Dict, List, Optional, cast

import reflex as rx
from gws_core.core.utils.logger import Logger
from typing_extensions import TypedDict

UNAUTHORIZED_ROUTE = "/unauthorized"
APP_CONFIG_FILENAME = 'app_config.json'


class StreamlitConfigDTO(TypedDict):
    app_dir_path: str
    source_ids: List[str]
    params: Optional[dict]
    requires_authentication: bool
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: Dict[str, str]


class QueryParamObject():

    def __init__(self, query_param_str: str):
        """Initialize the QueryParamObject with a query parameter string."""
        self.query_param_str = query_param_str
        self.params = self._parse_query_params()

    def _parse_query_params(self) -> Dict[str, str]:
        """Parse the query parameter string into a dictionary."""
        params = {}
        if self.query_param_str:
            for param in self.query_param_str.split('&'):
                key, value = param.split('=', 1)
                params[key] = value
        return params

    def get(self, key: str, default=None) -> Optional[str]:
        """Get a parameter value by key."""
        return self.params.get(key, default)


class ReflexMainStateBase2(rx.State):
    """Base State of Reflex. This state is used by normal app and virtual environment app.

    It is used to manage the app configuration, authentication, and parameters.
    """
    _app_config: dict = None
    _is_initialized: bool = False

    # None if the user is not authenticated
    authenticated_user_id: Optional[str] = None

    # Constant for dev mode
    DEV_MODE_USER_ACCESS_TOKEN_KEY = 'dev_mode_token'
    DEV_MODE_APP_ID = '1'

    @rx.event
    async def on_load(self):
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

        if not self._app_config:
            self._app_config = self._load_app_config()

        user_access_tokens = self._app_config.get('user_access_tokens', {})

        if not self.authenticated_user_id:
            self.authenticated_user_id = await self._check_user_token(user_access_tokens)

        requires_authentication = self._app_config.get('requires_authentication', False)

        if requires_authentication and not self.authenticated_user_id:
            # If the app requires authentication and the user is not authenticated,
            # redirect to the unauthorized page
            return rx.redirect(UNAUTHORIZED_ROUTE)

        self._is_initialized = True

    @rx.var
    def is_initialized_computed(self) -> bool:
        """Computed property for frontend access."""
        return self._is_initialized

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
            with open(app_config_path, 'r', encoding='utf-8') as file:
                return load(file)

        except Exception as e:
            raise ValueError(f"Error reading app config file: {e}")

    def _get_app_config_file_path(self) -> str:
        config_dir = os.environ.get('GWS_REFLEX_APP_CONFIG_DIR_PATH')
        if not config_dir:
            raise ValueError("GWS_REFLEX_APP_CONFIG_DIR_PATH environment variable is not set in production mode")

        app_id: str = None
        if self.is_dev_mode():
            app_id = self.DEV_MODE_APP_ID
        else:
            query_param = self.get_query_params()
            app_id = query_param.get('gws_app_id')
            if not app_id:
                # Return None and don't throw an error because this is called
                # during the build
                Logger.warning("gws_app_id query parameter is not set. This is normal during build")
                return None
                # raise ValueError("gws_app_id query parameter is not set")

        return os.path.join(config_dir, app_id, APP_CONFIG_FILENAME)

    async def _check_user_token(self, user_access_tokens: Dict[str, str]) -> Optional[str]:

        if self.is_dev_mode():
            return user_access_tokens.get(self.DEV_MODE_USER_ACCESS_TOKEN_KEY)

        query_params = self.get_query_params()

        url_token = query_params.get('gws_token')

        env_token = os.environ.get('GWS_REFLEX_TOKEN')

        if url_token != env_token:
            return None

        # load user id from access token
        user_access_token = self._get_user_access_token()
        if user_access_token is None:
            return None

        return user_access_tokens.get(user_access_token)

    def is_dev_mode(self) -> bool:
        """Check if the app is running in development mode."""
        return os.environ.get('GWS_REFLEX_DEV_MODE', 'false').lower() == 'true'

    async def get_app_config(self) -> StreamlitConfigDTO:
        """Get the app configuration."""
        if self._app_config is None:
            await self.on_load()
        # raise ValueError("App configuration is not loaded. Call on_load() first.")
        return cast(StreamlitConfigDTO, self._app_config)

    async def get_sources_ids(self) -> List[str]:
        """Get the source IDs from the app configuration."""
        source_ids = (await self.get_app_config()).get('source_ids')
        if source_ids is None:
            return []
        return source_ids

    def is_virtual_env_app(self) -> bool:
        """Check if the app is running in a virtual environment."""
        return os.environ.get('GWS_REFLEX_VIRTUAL_ENV', 'false').lower() == 'true'

    def get_query_params(self) -> QueryParamObject:
        """Get the query parameters from the app configuration."""
        return QueryParamObject(self.router.url.query)

    ##################### AUTHENTICATION #####################

    async def requires_authentication(self) -> bool:
        """Check if the app requires authentication."""
        return (await self.get_app_config()).get('requires_authentication', False)

    async def check_authentication(self) -> bool:
        if not self._is_initialized:
            return False
        if self.is_dev_mode():
            return True
        if not await self.requires_authentication():
            return True
        return self.authenticated_user_id is not None

    def _get_user_access_token(self) -> Optional[str]:
        """Get the user access token from the app configuration."""
        query_params = self.get_query_params()
        return query_params.get('gws_user_access_token')

    ####################### PARAMS #####################

    async def get_param(self, key: str, default=None) -> Optional[str]:
        """Get a parameter from the app configuration."""
        params = await self.get_params()
        return params.get(key, default)

    async def get_params(self) -> dict:
        """Get the parameters from the app configuration."""
        params = (await self.get_app_config()).get('params')
        if params is None:
            return {}
        return params
