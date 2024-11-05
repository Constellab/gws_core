import argparse
import importlib.util
import os
import sys
from typing import List, Optional

import streamlit as st
from pydantic import BaseModel

APP_CONFIG_FILENAME = 'streamlit_config.json'
APP_MAIN_FILENAME = 'main.py'


class StreamlitConfigDTO(BaseModel):
    app_dir_path: str
    source_ids: List[str]
    params: Optional[dict]


def import_streamlit_helper():
    """
    Method to make the streamlit_helper pyton module available in the sys path.
    Then module can be imported like this:
    from gws_streamlit_helper import StreamlitEnvLoader
    """
    if 'gws_streamlit_helper' not in sys.modules:
        streamlit_helper_folder = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_streamlit_helper"
        )
        sys.path.insert(0, streamlit_helper_folder)


@st.cache_data
def load_sources(source_ids: List[str]) -> List['Resource']:
    """
    Cached method to load the sources from the source ids.

    :return: list of resources
    :rtype: _type_
    """
    from gws_core import ResourceModel
    sources_ = []
    for source_path in source_ids:
        resource_model = ResourceModel.get_by_id_and_check(source_path)
        sources_.append(resource_model.get_resource())
    return sources_


parser = argparse.ArgumentParser()
parser.add_argument('--gws_token', type=str, default=None)
parser.add_argument('--app_dir', type=str, default=None)
parser.add_argument('--dev_mode', type=bool, default=False)
parser.add_argument('--dev_config_file', type=str, default=None)
args = parser.parse_args()

# Configure Streamlit
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

app_config_file: str = None
user_id: str = None

dev_mode: bool = args.dev_mode
if not dev_mode:
    # retreive the token from query params
    url_token = st.query_params.get('gws_token')
    if url_token != args.gws_token:
        st.error('Invalid token')
        st.stop()

    app_config_dir = args.app_dir
    if not app_config_dir:
        st.error('App dir not provided')
        st.stop()

    if not os.path.exists(app_config_dir):
        st.error(f"Config dir not found: {app_config_dir}")
        st.stop()

    # check the app path
    app_id = st.query_params.get('gws_app_id')
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

    # check the user id
    user_id = st.query_params.get('gws_user_id')
    if not user_id:
        st.error('User id not provided')
        st.stop()
else:
    app_config_file = args.dev_config_file
    if not app_config_file:
        st.error('Dev config file not provided')
        st.stop()

    if not os.path.exists(app_config_file):
        st.error(f"Dev config file not found: {app_config_file}")
        st.stop()


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

    </style>
""", unsafe_allow_html=True)

try:
    import_streamlit_helper()
except Exception as e:
    st.error(f"Error importing streamlit helper: {e}")
    st.stop()

# load and run the streamlit sub app
try:

    # load config from the app path
    config: StreamlitConfigDTO = None

    with open(app_config_file, 'r', encoding="utf-8") as file_path:
        str_json = file_path.read()
        config = StreamlitConfigDTO.model_validate_json(str_json)

    app_dir_abs_path = config.app_dir_path

    # if the app dir path is not absolute (usually on dev mode), make it absolute
    if not os.path.isabs(config.app_dir_path):
        # make the path absolute relative to the config file
        config_file_dir = os.path.dirname(app_config_file)
        app_dir_abs_path = os.path.join(config_file_dir, config.app_dir_path)
        print(
            f"app_dir_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {app_dir_abs_path}")

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

    spec = importlib.util.spec_from_file_location("module_name", app_main_path)
    if spec is None:
        st.error(f"Python script file not found: {app_main_path}")
        st.stop()
    module = importlib.util.module_from_spec(spec)

    # Load gws environment and log the user
    from gws_streamlit_helper.streamlit_env_loader import StreamlitEnvLoader
    with StreamlitEnvLoader(user_id, dev_mode):

        # load resources
        sources = load_sources(config.source_ids)

        # set the source paths and params in the module
        setattr(module, 'sources', sources)
        setattr(module, 'params', config.params)

        spec.loader.exec_module(module)
except Exception as e:
    st.error(f"Error loading python script: {e}")
    st.stop()
