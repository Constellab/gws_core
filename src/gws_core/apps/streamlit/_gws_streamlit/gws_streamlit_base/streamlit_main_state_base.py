"""Core bootstrap logic for initializing Streamlit apps."""

import os
from abc import ABC, abstractmethod
from json import load
from typing import Any, TypedDict, cast

import streamlit as st

from .streamlit_code_exchange import exchange_code_for_jwt


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

        print(f"[GWS DEBUG] initialize: bootstrap_initialized="
              f"{st.session_state.get('__gws_bootstrap_initialized__')!r} "
              f"user_id={st.session_state.get('__gws_user_id__')!r} "
              f"query_params={dict(st.query_params)!r}")

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

        # Check token in non-dev mode. Only AUTHENTICATED apps require the token: their
        # URL always carries it. PUBLIC apps have a bare, shareable URL (no token), so a
        # missing token must not block loading there.
        #
        # The gws_token gate only guards the legacy gws_user_access_token path. A gateway
        # handoff URL carries a single-use gws_code instead (the code is the credential,
        # verified server-side at exchange), and no gws_token — so skip the gate when a
        # gws_code is present.
        if (
            not cls.is_dev_mode()
            and cls.authentication_is_required()
            and not st.query_params.get("gws_code")
        ):
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

        # New auth path: a single-use gws_code exchanged for a JWT. The code is the credential
        # (verified server-side by the lab). Handled before the legacy opaque-token map lookup.
        if not cls.is_dev_mode():
            code_result = cls._exchange_code_if_present()
            if code_result == "success":
                return
            if code_result == "failed":
                # A gws_code was present but could not be exchanged: it is single-use and
                # short-lived, so this typically means the link was already opened or expired.
                # Report that accurately instead of falling through to "token not provided".
                if authentication_required:
                    st.error(
                        "This app link has expired or was already used. "
                        "Please reopen the app to get a fresh link."
                    )
                    st.stop()
                return  # anonymous access
            # code_result == "absent": fall through to the legacy token path below.

        user_access_tokens = config.get("user_access_tokens", {})
        user_access_token: str | None = None
        if cls.is_dev_mode():
            user_access_token = cls.DEV_MODE_USER_ACCESS_TOKEN_KEY
        else:
            # Legacy path: opaque user access token (kept for the backward-compat window while
            # both a gws_code and a gws_user_access_token are emitted).
            user_access_token = st.query_params.get("gws_user_access_token")

        if not user_access_token:
            if authentication_required:
                st.error("User access token not provided")
                st.stop()
            return  # anonymous access

        user_id = user_access_tokens.get(user_access_token)

        if not user_id:
            if authentication_required:
                st.error("Invalid user access token")
                st.stop()
            return  # anonymous access

        st.session_state["__gws_user_access_token__"] = user_access_token
        st.session_state["__gws_user_id__"] = user_id

    @classmethod
    def _exchange_code_if_present(cls) -> str:
        """Try to authenticate from a single-use gws_code in the URL.

        Returns one of:
          - "absent": no gws_code in the URL (caller falls through to the legacy token path)
          - "success": exchanged; JWT + user id stored in session, gws_code scrubbed from the URL
          - "failed": a gws_code was present but could not be exchanged (expired or already used)
        Distinguishing "failed" from "absent" lets the caller show an accurate message instead of
        the misleading "token not provided".
        """
        code = st.query_params.get("gws_code")
        print(f"[GWS DEBUG] _exchange_code_if_present: gws_code={code!r} "
              f"all_query_params={dict(st.query_params)!r}")
        if not code:
            return "absent"

        exchanged = exchange_code_for_jwt(cls.get_app_id(), code)
        print(f"[GWS DEBUG] exchange result: {exchanged!r} app_id={cls.get_app_id()!r}")
        if exchanged is None:
            return "failed"

        # the JWT becomes the user access token the app carries to the data lab API
        st.session_state["__gws_user_access_token__"] = exchanged.user_access_token
        st.session_state["__gws_user_id__"] = exchanged.user_id
        # scrub gws_code from the URL (single-use; keep it out of history/referrers)
        if "gws_code" in st.query_params:
            del st.query_params["gws_code"]
        return "success"

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
