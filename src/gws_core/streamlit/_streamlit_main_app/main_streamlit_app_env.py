import streamlit as st
from main_streamlit_app_runner import StreamlitMainAppRunner
from streamlite_app_info_state import StreamlitAppInfo, StreamlitAppInfoState

streamlit_app = StreamlitMainAppRunner()

streamlit_app.init()

if not StreamlitAppInfoState.is_initialized():

    config = streamlit_app.config

    # load resources
    source_paths = config['source_ids']

    StreamlitAppInfoState.set_app_info({
        'app_id': streamlit_app.get_app_id(),
        'user_access_token': streamlit_app.get_user_access_token(),
        'requires_authentication': streamlit_app.authentication_is_required(),
        'user_id': streamlit_app.load_user(),
        'sources': None,
        'source_paths': config['source_ids'],
        'params': config['params'],
    })

    # Force a rerun on first load to fix flickering
    # With tabs, if a user make the first action on a second tab, it swtich to the first tab
    # With spinner, if a spinner if showed on first action, there is the app duplicated in disabled
    # This force re-run to fix first action
    st.rerun()

app_info: StreamlitAppInfo = StreamlitAppInfoState.get_app_info()

streamlit_app.set_variable('source_paths', app_info['source_paths'])
streamlit_app.set_variable('params', app_info['params'])

try:
    streamlit_app.start_app()
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
    with st.popover('View details'):
        st.exception(e)
