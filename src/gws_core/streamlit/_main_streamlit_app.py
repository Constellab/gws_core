import argparse
import importlib.util
import os
import sys

import streamlit as st


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


parser = argparse.ArgumentParser()
parser.add_argument('--gws_token', type=str, default=None)
args = parser.parse_args()

# Configure Streamlit
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# retreive the token from query params
url_token = st.query_params.get('gws_token')
if url_token != args.gws_token:
    st.error('Invalid token')
    st.stop()

# check the app path
app_path = st.query_params.get('gws_app_path')
if not app_path:
    st.error('App path not provided')
    st.stop()

# check the user id
user_id = st.query_params.get('gws_user_id')
if not user_id:
    st.error('User id not provided')
    st.stop()

# Add custom css to hide the streamlit menu
st.markdown("""
    <style>
        .block-container {
            padding: 8px;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}

    </style>
""", unsafe_allow_html=True)

try:
    import_streamlit_helper()
except Exception as e:
    st.error(f"Error importing streamlit helper: {e}")
    st.stop()

# load and run the streamlit sub app
try:
    if not isinstance(app_path, str):
        st.error("Invalid app path")
        st.stop()

    if not os.path.exists(app_path):
        st.error(f"Python script file not found: {app_path}")
        st.stop()

    spec = importlib.util.spec_from_file_location("module_name", app_path)

    if spec is None:
        st.error(f"Python script file not found: {app_path}")
        st.stop()
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
except FileNotFoundError:
    st.error(f"Python script file not found: {app_path}")
    st.stop()
except Exception as e:
    st.error(f"Error loading python script: {e}")
    st.stop()
