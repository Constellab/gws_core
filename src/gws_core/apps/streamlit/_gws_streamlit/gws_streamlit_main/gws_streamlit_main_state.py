"""State class for registering GWS Streamlit apps."""

import os
import warnings

import streamlit as st
from gws_streamlit_base import StreamlitMainStateBase
from gws_streamlit_main.utils.streamlit_auth_context_loader import StreamlitAuthContextLoader

from gws_core import (
    CurrentUserService,
    LogContext,
    Resource,
    ResourceModel,
    Settings,
    User,
    UserService,
    manage,
)
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.auth_context import AuthContextApp


class StreamlitUserAuthInfo(BaseModelDTO):
    app_id: str
    user_access_token: str


class StreamlitMainState(StreamlitMainStateBase):
    """State manager for GWS Streamlit apps in normal mode."""

    @classmethod
    def _post_initialize(cls):
        """Load GWS environment and authenticate user."""

        # Initialize GWS environment if not already done
        if not manage.AppManager.gws_env_initialized:
            app_id = cls.get_app_id()

            # Inherit the parent process's log level (set by the CLI's --log-level
            # and forwarded via GWS_LOG_LEVEL), falling back to INFO when not set.
            log_level = os.environ.get("GWS_LOG_LEVEL") or "INFO"

            manage.AppManager.init_gws_env_and_db(
                main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
                log_level=log_level,
                log_context=LogContext.STREAMLIT,
                log_context_id=app_id,
                auth_context_loader=StreamlitAuthContextLoader(),
            )

        # Authenticate user in GWS system
        user_id = cls.get_current_user_id()
        user = UserService.get_by_id_or_none(user_id)
        if not user:
            raise Exception("User not authenticated, cannot find the user from the id")

        auth_context = AuthContextApp(app_id=cls.get_app_id(), user=user)
        CurrentUserService.set_auth_context(auth_context)

    @classmethod
    def register_streamlit_app(cls) -> None:
        """.. deprecated::
            register_streamlit_app is deprecated and will be removed in a future version.
            Use initialize() instead.

        Register and initialize a GWS Streamlit app.

        This calls StreamlitBootstrap.initialize() and loads resources from source_ids
        for non-virtual-env apps.

        Usage in user's main.py:
        ```python
        from gws_streamlit_main import StreamlitAppState

        sources, params = StreamlitAppState.register_streamlit_app()

        # Your Streamlit app code here
        st.title("My App")
        ```

        Returns:
            Tuple of (sources, params) loaded from app config
        """
        warnings.warn(
            "register_streamlit_app is deprecated and will be removed in a future version. "
            "Use initialize() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Initialize bootstrap (no return value)
        cls.initialize()

    @classmethod
    @st.cache_data
    def get_sources(cls) -> list["Resource"]:
        """Load resources from source IDs (cached)."""
        config = cls.get_app_config()
        source_ids = config.get("source_ids", [])
        if not source_ids:
            return []

        sources = []
        for source_id in source_ids:
            resource_model = ResourceModel.get_by_id_and_check(source_id)
            sources.append(resource_model.get_resource())
        return sources

    @classmethod
    @st.cache_data
    def get_and_check_current_user(cls) -> User:
        """Return the current connected user.
        If the app does not require authentication, the user will be the system user.
        To check if a real user is authenticated, use user_is_authenticated().

        :return: the current connected user
        :rtype: User | None
        """
        return CurrentUserService.get_and_check_current_user()

    @classmethod
    @st.cache_data
    def get_current_user(cls) -> User | None:
        """Return the current connected user.
        If the app does not require authentication, the user will be the system user.
        To check if a real user is authenticated, use user_is_authenticated().

        :return: the current connected user
        :rtype: User | None
        """
        return CurrentUserService.get_current_user()

    @classmethod
    def get_user_auth_info(cls) -> StreamlitUserAuthInfo:
        """Return the user auth info.
        This is useful to auth the user in custom components

        :return: the user auth info
        :rtype: StreamlitUserAuthInfo
        """
        return StreamlitUserAuthInfo(
            app_id=cls.get_app_id(), user_access_token=cls.get_user_access_token()
        )
