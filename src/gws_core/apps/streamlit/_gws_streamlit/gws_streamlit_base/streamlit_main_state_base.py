"""Core bootstrap logic for initializing Streamlit apps."""

import os
from abc import ABC, abstractmethod
from json import load
from typing import Any, TypedDict, cast

import streamlit as st


class StreamlitAppConfig(TypedDict):
    source_ids: list[str]
    params: dict | None
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: dict[str, str]


class StreamlitMainStateBase(ABC):
    """Bootstrap handler for GWS Streamlit apps.

    This class handles initialization, authentication, and configuration
    for Streamlit apps. It should be called at the top of the user's main.py.
    """

    APP_CONFIG_FILENAME = "app_config.json"
    DEV_MODE_APP_ID = "dev-app"
    DEV_MODE_USER_ACCESS_TOKEN_KEY = "dev_mode_token"

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize Streamlit app with GWS configuration.

        Usage in user's main.py:
        ```python
        from gws_streamlit_base import StreamlitBootstrap
        StreamlitBootstrap.initialize()
        ```

        Does not return sources/params - these are handled by the factory classes.
        """

        # 1. Configure Streamlit page first (enables st.spinner, st.error, etc.)
        cls._configure_page()

        if st.session_state.get("__gws_bootstrap_initialized__"):
            return

        with st.spinner("Initializing app..."):
            # 2. Load app configuration
            config = cls._load_app_config()
            st.session_state["__gws_bootstrap_config__"] = config

            # 3. Check authentication (sets user in session_state)
            cls._check_authentication(config)

            # 4. Post-initialization hook for subclasses
            cls._post_initialize()

            st.session_state["__gws_bootstrap_initialized__"] = True

    @classmethod
    @abstractmethod
    def _post_initialize(cls):
        """Post-initialization hook for subclasses to override.

        Called at the end of initialization. Subclasses can override this to perform
        additional setup like loading GWS environment.
        """
        pass

    @classmethod
    def _configure_page(cls):
        """Configure Streamlit page settings and custom CSS."""
        st.set_page_config(
            page_title="App",
            layout="wide",
            menu_items={},
            initial_sidebar_state=st.session_state.get("__gws_sidebar_state__", "expanded"),
        )

        # Add custom CSS (same as current implementation)
        st.markdown(
            """
            <style>
                html{
                    font-size: 14px;
                }
                .block-container {
                    padding: 8px;
                }

                /*
                  Hide the main streamlit menu and loader
                  We don't hide the complete header because, the toggle sidebar button is there
                */
                header {
                    background: transparent !important;
                    width: fit-content !important;

                }
                header :has(> .stMainMenu) {
                   display: none !important;
                }


                /* use same top and bottom padding for title to be able to align element with the title */
                h1, h2 {
                    padding: 0.5rem 0 !important;
                }
                h3, h5, h6 {
                    padding: 0.25rem 0 !important;
                }
                h4 {
                    padding: 0.40rem 0 !important;
                }
                p, ol, ul, dl{
                    margin: 0.25rem 0 !important;
                }
                .stButton button,
                .stLinkButton a {
                    border-width: 2px;
                    border-radius: 30px;
                }

                /*
                    Remove weird negative margin-bottom  that is used
                    to override the default column gap between element.
                    This margin is used for text and title elements.
                    It breaks the alignment so we remove it and reduce the padding
                    of headers and paragraphs to achieve the same result.
                */
                [data-testid="stMarkdownContainer"] {
                    margin-bottom: 0 !important;
                }
                /* Hide the container that only contain style. Without this they have a small height */
                .stElementContainer:has(.stMarkdown style) {
                    display: none;
                }

            </style>
        """,
            unsafe_allow_html=True,
        )

    @classmethod
    def _load_app_config(cls) -> dict:
        """Load app configuration from environment-specified path."""
        if st.session_state.get("__gws_app_config__"):
            return st.session_state["__gws_app_config__"]

        # Check token in non-dev mode
        if not cls.is_dev_mode():
            url_token = st.query_params.get("gws_token")
            env_token = os.environ.get("GWS_APP_TOKEN")
            if url_token != env_token:
                st.error("Invalid token")
                st.stop()

        # Get config directory from environment
        app_config_file = os.environ.get("GWS_APP_CONFIG_FILE_PATH")
        if not app_config_file:
            st.error("App config file path not provided")
            st.stop()

        # Build config path
        if not os.path.exists(app_config_file):
            st.error(f"App config file not found: {app_config_file}")
            st.stop()

        # Load config
        with open(app_config_file, encoding="utf-8") as f:
            config = load(f)

        st.session_state["__gws_app_config__"] = config
        return config

    @classmethod
    def _check_authentication(cls, config: StreamlitAppConfig):
        """Validate token and authenticate user."""
        if st.session_state.get("__gws_user_id__"):
            return  # Already authenticated

        user_access_tokens = config.get("user_access_tokens", {})
        user_access_token: str | None = None
        if cls.is_dev_mode():
            user_access_token = cls.DEV_MODE_USER_ACCESS_TOKEN_KEY
        else:
            # Check user access token
            user_access_token = st.query_params.get("gws_user_access_token")

        if not user_access_token:
            st.error("User access token not provided")
            st.stop()
        user_id = user_access_tokens.get(user_access_token)

        if not user_id:
            st.error("Invalid user access token")
            st.stop()

        st.session_state["__gws_user_access_token__"] = user_access_token
        st.session_state["__gws_user_id__"] = user_id

    @classmethod
    def get_app_config(cls) -> StreamlitAppConfig:
        """
        Get the loaded app configuration.

        Returns:
            dict: The app configuration
        """
        return st.session_state.get("__gws_bootstrap_config__", {})

    @classmethod
    def get_params(cls) -> dict[str, Any]:
        """
        Get the app parameters from the configuration.

        Returns:
            dict: The app parameters
        """
        config = cls.get_app_config()
        return cast(dict, config.get("params", {}))

    @classmethod
    def get_param(cls, key: str, default: Any = None) -> Any:
        """
        Get a specific app parameter by key.

        Args:
            key (str): The parameter key
            default (Any): The default value if the key is not found

        Returns:
            Any: The parameter value or default
        """
        params = cls.get_params()
        return params.get(key, default)

    @classmethod
    def get_app_id(cls) -> str:
        """Get app ID from environment or dev mode default."""
        if cls.is_dev_mode():
            return cls.DEV_MODE_APP_ID
        app_id = os.environ.get("GWS_APP_ID")
        if not app_id:
            raise ValueError("GWS_APP_ID environment variable is not set")
        return app_id

    @classmethod
    def is_dev_mode(cls) -> bool:
        """Check if running in dev mode."""
        return os.environ.get("GWS_IS_DEV_MODE", "false").lower() == "true"

    @classmethod
    def authentication_is_required(cls) -> bool:
        return os.environ.get("GWS_REQUIRES_AUTHENTICATION", "true").lower() == "true"

    @classmethod
    def get_user_access_token(cls) -> str:
        """Return the user access token

        :return: the user access token
        :rtype: str
        """
        return cast(str, st.session_state.get("__gws_user_access_token__"))

    @classmethod
    def get_current_user_id(cls) -> str:
        """Return the current connected user id.

        :return: the current connected user id
        :rtype: str | None
        """
        return cast(str, st.session_state.get("__gws_user_id__"))
