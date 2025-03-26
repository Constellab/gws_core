import argparse
import importlib.util
import os
import sys
from json import load
from types import ModuleType
from typing import Any, Dict, List, Optional

import streamlit as st
from typing_extensions import TypedDict

APP_CONFIG_FILENAME = 'streamlit_config.json'
APP_MAIN_FILENAME = 'main.py'


class StreamlitConfigDTO(TypedDict):
    app_dir_path: str
    source_ids: List[str]
    params: Optional[dict]
    requires_authentication: bool
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: Dict[str, str]


class StreamlitMainAppRunner:
    """Class to execute code on start of streamlit app to load the app file and config file.
    It is use in normal streamlit app and env streamlit app.

    :return: _description_
    :rtype: _type_
    """

    module: ModuleType = None
    spec = None
    config: StreamlitConfigDTO = None

    gws_token: str = None
    app_dir: str = None
    dev_mode: bool = False
    dev_config_file: str = None

    def init(self) -> None:
        """ Check the parameters (token) and loaf the config and app file"""

        # Configure Streamlit
        st.set_page_config(
            page_title="Dashboard",
            layout="wide",
            menu_items={},  # hide the menu
            initial_sidebar_state=st.session_state.get('__gws_sidebar_state__', 'expanded'),
        )

        # Add custom css to hide the streamlit menu
        st.markdown("""
            <style>
                .block-container {
                    padding: 8px;
                }
                /* hide the streamlit header menu */
                header {
                    display: none !important;
                }
                h1 {
                    padding: 0;
                }
                /* Hide the container that only contain style. Without this they have a small height */
                .stElementContainer:has(.stMarkdown style) {
                    display: none;
                }

            </style>
        """, unsafe_allow_html=True)

        self._load_args()
        app_config_file: str = self._load_app_config_file()

        self.module = self._load_app(app_config_file)
        self.load_user()

    def _load_args(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument('--gws_token', type=str, default=None)
        parser.add_argument('--app_dir', type=str, default=None)
        parser.add_argument('--dev_mode', type=bool, default=False)
        parser.add_argument('--dev_config_file', type=str, default=None)
        args = parser.parse_args()
        self.gws_token = args.gws_token
        self.app_dir = args.app_dir
        self.dev_mode = args.dev_mode
        self.dev_config_file = args.dev_config_file

    def set_variable(self, name: str, value: Any) -> None:
        setattr(self.module, name, value)
        # also set the variable in the session state
        st.session_state[f'__{name}__'] = value

    def start_app(self) -> None:
        self.spec.loader.exec_module(self.module)

    def load_user(self) -> str:
        # skip user load if authentication is not required
        if not self.authentication_is_required():
            return None
        if self.dev_mode:
            return None

        if st.session_state.get('__gws_user_id__'):
            return st.session_state['__gws_user_id__']

        user_access_token = st.query_params.get('gws_user_access_token')
        if not user_access_token:
            st.error('User access token not provided')
            st.stop()

        # retrieve the list of users that can access the app
        user_access_tokens = self.config.get('user_access_tokens', {})
        user_id = user_access_tokens.get(user_access_token)
        if not user_id:
            st.error('Invalid user access token')
            st.stop()

        # save the user id and app config file in the session state
        st.session_state['__gws_user_id__'] = user_id

        return user_id

    def _load_app_config_file(self) -> str:

        if st.session_state.get('__app_config_file__'):
            return st.session_state['__app_config_file__']

        if self.dev_mode:
            app_config_file = self.dev_config_file
            if not app_config_file:
                st.error('Dev config file not provided')
                st.stop()

            if not os.path.exists(app_config_file):
                st.error(f"Dev config file not found: {app_config_file}")
                st.stop()
        else:
            # retreive the token from query params
            url_token = st.query_params.get('gws_token')
            if url_token != self.gws_token:
                st.error('Invalid token')
                st.stop()

            app_config_dir = self.app_dir
            if not app_config_dir:
                st.error('App dir not provided')
                st.stop()

            if not os.path.exists(app_config_dir):
                st.error(f"Config dir not found: {app_config_dir}")
                st.stop()

            # check the app path
            app_id = self.get_app_id()
            if not app_id:
                st.error('App id not provided')
                st.stop()

            # check if the app id folder exists
            app_config_folder = os.path.join(app_config_dir, app_id)
            if not os.path.exists(app_config_folder) or not os.path.isdir(app_config_folder):
                st.error('App config folder not found or is not a folder')
                st.stop()

            app_config_file = os.path.join(app_config_folder, APP_CONFIG_FILENAME)
            if not os.path.exists(app_config_file):
                st.error('App config file not found')
                st.stop()

        st.session_state['__app_config_file__'] = app_config_file

        return app_config_file

    def _load_app(self, app_config_file: str) -> ModuleType:
        try:

            # load config from the app path
            with open(app_config_file, 'r', encoding="utf-8") as file_path:
                self.config = load(file_path)

            app_dir_abs_path = self.config['app_dir_path']

            # if the app dir path is not absolute (usually on dev mode), make it absolute
            if not os.path.isabs(app_dir_abs_path):
                # make the path absolute relative to the config file
                config_file_dir = os.path.dirname(app_config_file)
                app_dir_abs_path = os.path.join(config_file_dir, app_dir_abs_path)
                # print(
                #     f"app_dir_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {app_dir_abs_path}")

            if not os.path.exists(app_dir_abs_path) or not os.path.isdir(app_dir_abs_path):
                st.error(f"App dir not found: {app_dir_abs_path}")
                st.stop()

            # load the folder as module if not already in sys path
            if app_dir_abs_path not in sys.path:
                sys.path.insert(0, app_dir_abs_path)

            app_main_path = os.path.join(app_dir_abs_path, APP_MAIN_FILENAME)

            if not os.path.exists(app_main_path):
                st.error(
                    f"Main python script file not found: {app_main_path}. Please make sure you have a main.py file in the app folder.")
                st.stop()

            # load the module ('main' is the file name)
            self.spec = importlib.util.spec_from_file_location("main", app_main_path)
            if self.spec is None:
                st.error(f"Python script file not found: {app_main_path}")
                st.stop()

            # due to dynamic import, streamlit lose track of the module so it doesn't refresh it correctly when the file changes
            # only the main.py file is refresh because it is load dynamically but its dependencies are not
            return importlib.util.module_from_spec(self.spec)

        except Exception as e:
            st.error(f"Error loading python script: {e}")
            st.exception(e)
            st.stop()

    def get_app_id(self) -> str:
        return st.query_params.get('gws_app_id')

    def authentication_is_required(self) -> bool:
        return self.config.get('requires_authentication')
