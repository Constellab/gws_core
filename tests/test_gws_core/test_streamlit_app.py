from gws_core.apps.app_dto import AppProcessStatus
from gws_core.apps.apps_manager import AppsManager
from gws_core.apps.streamlit.streamlit_process import StreamlitProcess
from gws_core.apps.streamlit.streamlit_resource import StreamlitResource
from gws_core.config.config_params import ConfigParams
from gws_core.impl.table.table import Table
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.test.base_test_case import BaseTestCase
from pandas import DataFrame


# test_streamlit_app
class TestStreamlitApp(BaseTestCase):
    def test_streamlit_resource(self):
        df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

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
        streamlit_resource: StreamlitResource = StreamlitResource()
        streamlit_resource.set_streamlit_code(streamlit_code)
        streamlit_resource.add_resource(resource_model.get_resource())
        resource_model = ResourceModel.save_from_resource(
            streamlit_resource, origin=ResourceOrigin.UPLOADED
        )

        streamlit_resource = resource_model.get_resource()
        # make the check faster to avoid test block
        StreamlitProcess.CHECK_RUNNING_INTERVAL = 3

        try:
            # generate the streamlit app
            streamlit_resource.default_view(ConfigParams())

            streamlit_process = AppsManager.find_app_by_resource_model_id(
                streamlit_resource.get_model_id()
            )

            if streamlit_process is None:
                self.fail("No streamlit process found")

            streamlit_process.wait_for_start()
            if not streamlit_process.is_running():
                self.fail("Streamlit process is not running")

            # check if the app is running
            self.assertTrue(streamlit_process.call_health_check())

            status = streamlit_process.get_status_dto()
            self.assertEqual(status.status, AppProcessStatus.RUNNING)
            self.assertEqual(status.app.app_resource_id, streamlit_resource.get_model_id())

            AppsManager.stop_all_processes()

            # check if the app is running
            self.assertFalse(streamlit_process.call_health_check())
            self.assertFalse(streamlit_process.subprocess_is_running())
        finally:
            AppsManager.stop_all_processes()
