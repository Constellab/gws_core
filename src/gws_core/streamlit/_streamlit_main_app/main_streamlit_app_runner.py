import argparse
import importlib.util
import os
import sys
from json import load
from typing import Any, Dict, List, Optional

import streamlit as st
from typing_extensions import TypedDict

APP_CONFIG_FILENAME = 'app_config.json'
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

    spec = None
    config: StreamlitConfigDTO = None

    gws_token: str = None
    app_dir: str = None
    dev_mode: bool = False
    dev_config_file: str = None

    app_dir_path: str = None
    app_main_path: str = None
    variables: Dict[str, Any] = {}

    def init(self) -> None:
        """ Check the parameters (token) and loaf the config and app file"""

        # Configure Streamlit
        st.set_page_config(
            page_title="App",
            layout="wide",
            menu_items={},  # hide the menu
            initial_sidebar_state=st.session_state.get('__gws_sidebar_state__', 'expanded'),
        )

        # Add custom css to hide the streamlit menu
        st.markdown("""
            <style>
                html{
                    font-size: 14px;
                }
                .block-container {
                    padding: 8px;
                }
                /* hide the streamlit header menu */
                header {
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
        """, unsafe_allow_html=True)

        self._load_args()
        app_config_file: str = self._load_app_config_file()

        self._load_app(app_config_file)
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
        self.variables[name] = value

    def start_app(self) -> None:
        # Add the parent directory of the app to sys.path so Python can find the package
        parent_dir = os.path.dirname(self.app_dir_path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        module_name = os.path.basename(self.app_dir_path)

        # Check if module already exists with a different path
        if module_name in sys.modules:
            existing_module = sys.modules[module_name]
            if hasattr(existing_module, '__file__') and existing_module.__file__:
                existing_path = os.path.dirname(existing_module.__file__)
                if os.path.abspath(existing_path) != os.path.abspath(self.app_dir_path):
                    raise ImportError(
                        f"There is 2 streamlit running app stored in different location with the name '{module_name}'. "
                        f"Original running app from : {existing_path}, current app from: {self.app_dir_path}. "
                        f"The 2 apps cannot be run simultaneously. Please stop the original app before starting the new one. "
                        f"If you are the author of the app, please rename one of the app to avoid this conflict. "
                        f"You can stop the app in Settings > Monitoring > Other > Running Apps.")

        # First, we need to make sure the directory is treated as a package
        # by ensuring it has an __init__.py file
        init_file = os.path.join(self.app_dir_path, '__init__.py')
        if not os.path.exists(init_file):
            # Create an empty __init__.py file if it doesn't exist
            with open(init_file, 'w', encoding='utf-8') as f:
                pass

        try:
            # Import the package first
            importlib.import_module(module_name)

            # Create the main module spec but don't execute it yet
            main_module_name = f"{module_name}.main"
            main_spec = importlib.util.find_spec(main_module_name)

            if main_spec is None:
                raise ImportError(f"Could not find spec for {main_module_name}")

            # Create the module from spec
            main_module = importlib.util.module_from_spec(main_spec)

            # Set the sources and params variables BEFORE executing the module
            for key, value in self.variables.items():
                setattr(main_module, key, value)

            # Add the module to sys.modules so it can be imported by other modules
            sys.modules[main_module_name] = main_module

            # Now execute the module
            main_spec.loader.exec_module(main_module)

        except ImportError as e:
            st.error(f"Failed to import module {module_name}: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Error starting app: {e}")
            st.exception(e)
            st.stop()

    def load_user(self) -> str:
        # skip user load if authentication is not required
        if self.dev_mode:
            return None

        if st.session_state.get('__gws_user_id__'):
            return st.session_state['__gws_user_id__']

        user_access_token = self.get_user_access_token()
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

    def _load_app(self, app_config_file: str):
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

            self.app_main_path = app_main_path
            # clean the path to remove trailing slash if any
            if app_dir_abs_path.endswith('/'):
                app_dir_abs_path = app_dir_abs_path[:-1]
            self.app_dir_path = app_dir_abs_path

        except Exception as e:
            st.error(f"Error loading python script: {e}")
            st.exception(e)
            st.stop()

    def get_app_id(self) -> str:
        return st.query_params.get('gws_app_id')

    def get_user_access_token(self) -> str:
        return st.query_params.get('gws_user_access_token')

    def authentication_is_required(self) -> bool:
        return self.config.get('requires_authentication')
