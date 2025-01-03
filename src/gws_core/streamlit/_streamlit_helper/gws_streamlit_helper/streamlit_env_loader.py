import os
import sys
from typing import Optional

import streamlit as st


class StreamlitEnvLoader:
    """
    Class that support with statement to load the gws environment in streamlit app.
    Inside the with statement the gws environment is loaded and the current user is set.
    """

    user_id: str = None

    def __init__(self, user_id: str = None) -> None:
        self.user_id = user_id

    def __enter__(self):

        self._load_env()

        from gws_core import CurrentUserService, User

        user: Optional[User] = None

        if self.user_id is None:
            user = User.get_sysuser()
        else:
            user = User.get_by_id(self.user_id)

        if not user:
            st.error('User not found')
            st.stop()

        # Authenticate sys user because in S3 server we don't have a user
        CurrentUserService.set_current_user(user)
        # Code to set up and acquire resources
        return self  # You can return an object that you want to use in the with block

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

                from gws_core import Settings, manage
                manage.AppManager.init_gws_env(
                    main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
                    log_level='INFO')
