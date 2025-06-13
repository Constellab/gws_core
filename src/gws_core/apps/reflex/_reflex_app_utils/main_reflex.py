import os
from json import load
from typing import Dict, List, Optional

import reflex as rx
from typing_extensions import TypedDict


# TODO set this file in a private folder to avoid loading rx on start
class StreamlitConfigDTO(TypedDict):
    app_dir_path: str
    source_ids: List[str]
    params: Optional[dict]
    requires_authentication: bool
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: Dict[str, str]


class ReflexAuthenticationState(rx.State):
    app_config: dict = None
    requires_authentication: bool = True
    is_initialized: bool = False

    @rx.var
    def is_authenticated(self) -> bool:
        url_token = self.router.page.params.get('gws_token')

        env_token = os.environ.get('GWS_TOKEN')

        return url_token == env_token

    def on_load(self):

        app_config: StreamlitConfigDTO = self._load_app_config()
        self.app_config = app_config

        self.requires_authentication = app_config['requires_authentication']

        self.is_initialized = True

        if self.requires_authentication and not self.is_authenticated:
            # If the app requires authentication and the user is not authenticated,
            # redirect to the unauthorized page
            return rx.redirect("/unauthorized")

    def _load_app_config(self) -> StreamlitConfigDTO:
        """Load the app configuration from the environment variable."""
        app_config_path = os.environ.get('GWS_APP_CONFIG_FILE_PATH')
        if not app_config_path:
            raise ValueError("GWS_APP_CONFIG_FILE_PATH environment variable is not set")

        if not os.path.exists(app_config_path):
            raise FileNotFoundError(f"App config file not found at {app_config_path}")

        try:
            with open(app_config_path, 'r', encoding='utf-8') as file:
                return load(file)

        except Exception as e:
            raise ValueError(f"Error reading app config file: {e}")


def _unauthorized_page():
    return rx.box(
        rx.heading("Unauthorized", font_size="2em"),
        rx.text("You are not authorized to view this page."),
    )


def add_unauthorized_page(app: rx.App):
    """Add the unauthorized page to the app."""
    app.add_page(_unauthorized_page, route="/unauthorized", title="Unauthorized")
