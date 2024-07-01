

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.impl.table.table import Table
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.gtest import GTest
from gws_core.user.current_user_service import AuthenticateUser


# test_streamlit_app
class TestStreamlitApp(BaseTestCase):

    def test_streamlit_resource(self):
        df = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        table = Table(df)
        resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

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

if sources:
    st.write(sources[0].get_data())
"""

        streamlit_resource = StreamlitResource(streamlit_code)
        streamlit_resource.add_resource(resource_model.get_resource())
        # make the check faster to avoid test block
        StreamlitAppManager.CHECK_RUNNING_INTERVAL = 3

        try:
            with AuthenticateUser(GTest.get_test_user()):
                # generate the streamlit app
                streamlit_resource.default_view(ConfigParams())

                # check if the app is running
                self.assertTrue(StreamlitAppManager.call_health_check())

                status = StreamlitAppManager.get_status_dto()
                self.assertEqual(status.status, 'RUNNING')
                self.assertEqual(len(status.running_apps), 1)
                self.assertEqual(status.running_apps[0].resource_id, streamlit_resource.uid)

                StreamlitAppManager.stop_main_app()

                # check if the app is running
                self.assertFalse(StreamlitAppManager.call_health_check())
        finally:
            StreamlitAppManager.stop_main_app()
