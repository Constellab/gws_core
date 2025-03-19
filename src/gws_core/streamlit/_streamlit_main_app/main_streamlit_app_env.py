import streamlit as st
from main_streamlit_app_runner import StreamlitMainAppRunner

streammlit_app = StreamlitMainAppRunner()

streammlit_app.init()

config = streammlit_app.config

# load resources
source_paths = config['source_ids']

streammlit_app.set_variable('source_paths', source_paths)
streammlit_app.set_variable('params', config['params'])

try:
    streammlit_app.start_app()
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
    with st.popover('View details'):
        st.exception(e)
