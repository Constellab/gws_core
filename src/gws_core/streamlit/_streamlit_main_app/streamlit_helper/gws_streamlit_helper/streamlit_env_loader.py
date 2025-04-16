import os
import sys

import streamlit as st


class StreamlitEnvLoader:
    """
    Class that support with statement to load the gws environment in streamlit app.
    Inside the with statement the gws environment is loaded and the current user is set.
    """

    app_id: str = None
    dev_mode: bool = False
    user_id: str = None

    def __init__(self, app_id: str,
                 dev_mode: bool,
                 user_id: str = None) -> None:
        self.app_id = app_id
        self.dev_mode = dev_mode
        self.user_id = user_id

    def __enter__(self):

        self._load_env()

        # Authenticate user
        self._authenticate_user()

        # Code to set up and acquire resources
        return self  # You can return an object that you want to use in the with block

    def _authenticate_user(self):
        """Authenticate the user.
        If the user was already initialized in streamlit, it will be used.
        Otherwise the connected user will be used and is required
        """
        from gws_core import CurrentUserService, User, UserService
        from gws_core.streamlit import StreamlitState

        user: User = StreamlitState.get_current_user()

        # if the user was not already authenticated
        if not user:
            # get the connected user
            user = None
            if self.dev_mode:
                user = User.get_and_check_sysuser()
            else:
                user = UserService.get_or_import_user_info(self.user_id)
            if not user:
                raise Exception("Cannot authenticate user")

            # Set the current user in the streamlit state
            StreamlitState.set_current_user(user)

        # Authenticate user
        CurrentUserService.set_current_user(user)

        # Set the running context as streamlit
        CurrentUserService.set_streamlit_context()

    def __exit__(self, exc_type, exc_value, traceback):
        # remove the current user
        from gws_core import CurrentUserService
        CurrentUserService.set_current_user(None)

    def _load_env(self):
        if 'gws_core' not in sys.modules:
            with st.spinner('Initializing dashboard...'):
                core_lib_path = "/lab/user/bricks/gws_core/src"
                if not os.path.exists(core_lib_path):
                    core_lib_path = "/lab/.sys/bricks/gws_core/src"
                    if not os.path.exists(core_lib_path):
                        raise Exception("Cannot find gws_core brick")
                sys.path.insert(0, core_lib_path)

                from gws_core import LogContext, Settings, manage
                manage.AppManager.init_gws_env(
                    main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
                    log_level='INFO', log_context=LogContext.STREAMLIT, log_context_id=self.app_id)
