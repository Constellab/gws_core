

from unittest import TestCase

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
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
        streamlit_resource._model_id = '1'

        # generate the streamlit app
        streamlit_resource.default_view(ConfigParams())

        # check if the app is running
        self.assertTrue(StreamlitAppManager.call_health_check())

        status = StreamlitAppManager.get_status_dto()
        self.assertEqual(status.status, 'RUNNING')
        self.assertEqual(len(status.running_apps), 1)
        self.assertEqual(status.running_apps[0].resource_id, streamlit_resource._model_id)

        StreamlitAppManager.stop_main_app()

        # check if the app is running
        self.assertFalse(StreamlitAppManager.call_health_check())
