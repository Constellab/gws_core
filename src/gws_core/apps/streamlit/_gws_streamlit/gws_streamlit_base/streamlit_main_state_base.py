"""Core bootstrap logic for initializing Streamlit apps."""

import os
from abc import ABC, abstractmethod
from json import load
from typing import Any, TypedDict, cast

import streamlit as st

from .streamlit_code_exchange import exchange_code_for_jwt, validate_jwt_for_user

# Name of the host session cookie holding the JWT, set by the app-host /gws-login endpoint (nginx
# -> core-api) and read here via st.context.cookies so auth survives a fresh page load (F5 / new
# tab). Mirrors AppGatewayService.APP_JWT_COOKIE_NAME (this module cannot import gws_core).
_APP_JWT_COOKIE_NAME = "gws_app_jwt"

# Query-param name carrying the single-use handoff code in the app URL (iframe / direct link
# initial load). Mirrors AppGatewayService.GWS_CODE_QUERY_PARAM (this module cannot import
# gws_core).
_GWS_CODE_QUERY_PARAM = "gws_code"


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
    # Fixed token always provisioned for the system user by the launch side. Mirrors
    # AppProcess.SYSTEM_USER_ACCESS_TOKEN_KEY (this module cannot import gws_core, so the
    # literal is duplicated). Used by components opting into fallback_to_system_user.
    SYSTEM_USER_ACCESS_TOKEN_KEY = "system_user_token"

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

        # Auth is established by the host session cookie (gws_app_jwt) set by the app-host
        # /gws-login endpoint and validated in _check_authentication — there is no longer a
        # gws_token gate here (the app never receives gws_token; the cookie is the credential).

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
        """Validate token and authenticate user.

        AUTHENTICATED apps hard-require a valid user access token (blocking on failure).
        PUBLIC apps run anonymously: a missing or invalid token leaves no user
        authenticated instead of blocking.
        """
        if st.session_state.get("__gws_user_id__"):
            return  # Already authenticated

        authentication_required = cls.authentication_is_required()

        # A PUBLIC app never authenticates a user, even in dev mode, so it simulates a
        # public prod app.
        if not authentication_required:
            return  # anonymous access

        # Dev mode: authenticate via the fixed dev sentinel token in the app config.
        if cls.is_dev_mode():
            user_id = config.get("user_access_tokens", {}).get(cls.DEV_MODE_USER_ACCESS_TOKEN_KEY)
            if user_id:
                st.session_state["__gws_user_access_token__"] = cls.DEV_MODE_USER_ACCESS_TOKEN_KEY
                st.session_state["__gws_user_id__"] = user_id
            return

        # Prod initial load: a single-use gws_code in the URL (iframe embed in the lab, or a
        # direct/bookmarked link opened without the host cookie yet). Exchange it for a JWT.
        if cls._authenticate_from_url_code():
            return

        # Prod page reload (F5 / new tab): no code in the URL, but the host session cookie
        # (gws_app_jwt) set by the app-host /gws-login endpoint is still sent. Read + validate it.
        if cls._authenticate_from_cookie_jwt():
            return

        if authentication_required:
            st.error(
                "Not authenticated. Please (re)open the app from its link to sign in."
            )
            st.stop()
        # PUBLIC: anonymous access

    @classmethod
    def _authenticate_from_url_code(cls) -> bool:
        """Try to authenticate from a single-use gws_code in the app URL.

        This is the initial-load credential: the lab embeds the app in an iframe (or a direct
        link is opened) with ?gws_code=… . The code is exchanged for a JWT, stored in session,
        and scrubbed from the URL so it is not reused or kept in history. Returns True on success
        (user stored in session), False when there is no code or the exchange fails.
        """
        code = st.query_params.get(_GWS_CODE_QUERY_PARAM)
        if not code:
            return False

        exchanged = exchange_code_for_jwt(cls.get_app_id(), code)
        # single-use: drop it from the URL regardless of the outcome so a reload can't retry it
        if _GWS_CODE_QUERY_PARAM in st.query_params:
            del st.query_params[_GWS_CODE_QUERY_PARAM]
        if not exchanged:
            return False

        st.session_state["__gws_user_access_token__"] = exchanged.user_access_token
        st.session_state["__gws_user_id__"] = exchanged.user_id
        return True

    @classmethod
    def _authenticate_from_cookie_jwt(cls) -> bool:
        """Try to authenticate from the JWT stored in the gws_app_jwt cookie.

        Runs on a fresh page load (F5 / new tab), where session_state is gone and there is no
        one-time code, but the cookie set on the first load is still sent by the browser. The JWT
        is read synchronously via st.context.cookies and validated by the lab. Returns True on
        success (user stored in session), False otherwise.
        """
        jwt = st.context.cookies.get(_APP_JWT_COOKIE_NAME)
        if not jwt:
            return False

        user_id = validate_jwt_for_user(cls.get_app_id(), jwt)
        if not user_id:
            return False

        st.session_state["__gws_user_access_token__"] = jwt
        st.session_state["__gws_user_id__"] = user_id
        return True

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
    def get_access_mode(cls) -> str:
        """Return the app access mode (AUTHENTICATED / PUBLIC).

        Read as a plain string from the GWS_APP_ACCESS_MODE env var so gws_streamlit_base
        stays free of any gws_core import (it may run in a virtual env without gws_core).
        Defaults to AUTHENTICATED.
        """
        return os.environ.get("GWS_APP_ACCESS_MODE", "AUTHENTICATED")

    @classmethod
    def authentication_is_required(cls) -> bool:
        return cls.get_access_mode() == "AUTHENTICATED"

    @classmethod
    def get_user_access_token(cls) -> str | None:
        """Return the user access token

        :return: the user access token
        :rtype: str | None
        """
        return cast("str | None", st.session_state.get("__gws_user_access_token__"))

    @classmethod
    def get_current_user_id(cls) -> str | None:
        """Return the current connected user id, or None for an anonymous app.

        :return: the current connected user id
        :rtype: str | None
        """
        return cast("str | None", st.session_state.get("__gws_user_id__"))

    @classmethod
    def get_system_user_access_token(cls) -> str | None:
        """Return the access token of the system user, if the launch side provisioned one.

        The token is provisioned for every non-dev app (stored in the app config but never
        in the URL). It lets front components fall back to running their API requests as the
        system user. Returns None if it is not available (e.g. a dev-mode app).

        :return: the system user access token, or None
        :rtype: str | None
        """
        user_access_tokens = cls.get_app_config().get("user_access_tokens", {})
        if cls.SYSTEM_USER_ACCESS_TOKEN_KEY in user_access_tokens:
            return cls.SYSTEM_USER_ACCESS_TOKEN_KEY
        return None
