import argparse
import importlib.util

import streamlit as st

parser = argparse.ArgumentParser()
parser.add_argument('--gws_app_path', type=str, default=None)
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

# Add custom css to hide the streamlit menu
st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        .block-container {
            padding: 16px;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}

    </style>
""", unsafe_allow_html=True)

# load and run the streamlit sub app
try:
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
