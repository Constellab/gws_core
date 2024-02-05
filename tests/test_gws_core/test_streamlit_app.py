# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest import TestCase

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_resource import StreamlitResource


# test_streamlit_app
class TestStreamlitApp(TestCase):

    def test_streamlit_resource(self):
        df = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        temp_folder = Settings.make_temp_dir()

        # export the dataframe to a csv file
        file_path = temp_folder + "/test.csv"
        df.to_csv(file_path)

        # create a streamlit resource
        streamlit_code = """
import streamlit as st
import pandas as pd

# Your Streamlit app code here
st.title("Embedded Streamlit App")
st.write('Sources path:', sources)

@st.cache_data
def long_running_function(file):
    st.write("No caching")
    return

# show a table from file_path which is a csv file full width
if sources:
    df = pd.read_csv(sources[0])
    st.write(df)
"""

        streamlit_resource = StreamlitResource(streamlit_code)
        streamlit_resource.add_resource(File(file_path), unique_name="test.csv")

        # generate the streamlit app
        streamlit_resource.default_view(ConfigParams())

        # streamlit_app = StreamlitAppManager.create_or_get_app('1')
        # streamlit_app.set_fs_node_paths([file_path])
        # streamlit_app.set_streamlit_code(streamlit_code)
        # url = streamlit_app.generate_app()

        # check if the app is running
        ExternalApiService.get(f"http://localhost:{StreamlitAppManager.MAIN_APP_PORT}/healthz")

        StreamlitAppManager.stop_main_app()

        # check if the app is running
        with self.assertRaises(Exception):
            ExternalApiService.get(f"http://localhost:{StreamlitAppManager.MAIN_APP_PORT}/healthz",
                                   raise_exception_if_error=False)
