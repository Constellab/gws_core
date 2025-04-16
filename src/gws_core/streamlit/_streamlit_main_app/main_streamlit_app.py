import os
import sys
from typing import List

import streamlit as st
from main_streamlit_app_runner import StreamlitMainAppRunner
from streamlite_app_info_state import StreamlitAppInfo, StreamlitAppInfoState


def import_streamlit_helper():
    """
    Method to make the streamlit_helper pyton module available in the sys path.
    Then module can be imported like this:
    from gws_streamlit_helper import StreamlitEnvLoader
    """
    if 'gws_streamlit_helper' not in sys.modules:
        streamlit_helper_folder = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "streamlit_helper"
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


def start_app(streamlit_app: StreamlitMainAppRunner) -> None:
    from gws_streamlit_helper.streamlit_env_loader import StreamlitEnvLoader

    # Load gws environment and log the user

    with StreamlitEnvLoader(streamlit_app.get_app_id(),
                            streamlit_app.dev_mode,
                            streamlit_app.load_user()):

        from gws_core.streamlit import StreamlitContainers

        if not StreamlitAppInfoState.is_initialized():

            config = streamlit_app.config

            # load resources
            sources = load_sources(config['source_ids'])

            StreamlitAppInfoState.set_app_info({
                'app_id': streamlit_app.get_app_id(),
                'user_access_token': streamlit_app.get_user_access_token(),
                'requires_authentication': streamlit_app.authentication_is_required(),
                'user_id': streamlit_app.load_user(),
                'sources': sources,
                'source_paths': None,
                'params': config['params'],
            })

        app_info: StreamlitAppInfo = StreamlitAppInfoState.get_app_info()

        streamlit_app.set_variable('sources', app_info['sources'])
        streamlit_app.set_variable('params', app_info['params'])

        try:
            streamlit_app.start_app()
        except Exception as e:
            from gws_core import Logger
            Logger.log_exception_stack_trace(e)
            StreamlitContainers.exception_container(key='main-exception-handler',
                                                    error_text=f"Unexpected error: {str(e)}",
                                                    exception=e)


streamlit_main_app = StreamlitMainAppRunner()

streamlit_main_app.init()

try:
    import_streamlit_helper()
except Exception as e:
    st.error(f"Error importing streamlit helper: {e}")
    st.stop()

start_app(streamlit_main_app)
