import os
import sys
from typing import List

import streamlit as st
from main_streamlit_app_runner import StreamlitMainAppRunner


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


def start_app(streammlit_app: StreamlitMainAppRunner) -> None:
    from gws_streamlit_helper.streamlit_env_loader import StreamlitEnvLoader

    # Load gws environment and log the user

    with StreamlitEnvLoader(streammlit_app.load_user()):

        config = streammlit_app.config

        # load resources
        sources = load_sources(config['source_ids'])

        streammlit_app.set_variable('sources', sources)
        streammlit_app.set_variable('params', config['params'])

        streammlit_app.start_app()


streammlit_app = StreamlitMainAppRunner()

streammlit_app.init()

try:
    import_streamlit_helper()
except Exception as e:
    st.error(f"Error importing streamlit helper: {e}")
    st.stop()

start_app(streammlit_app)
