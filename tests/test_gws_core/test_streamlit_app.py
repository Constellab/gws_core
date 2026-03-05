from gws_core.impl.apps.streamlit_showcase.generate_streamlit_showcase_app import (
    GenerateStreamlitShowcaseApp,
)
from gws_core.test.app_tester import AppTester
from gws_core.test.base_test_case import BaseTestCase


# test_streamlit_app
class TestStreamlitApp(BaseTestCase):
    def test_streamlit_resource(self):
        AppTester.test_app_from_task(
            test_case=self,
            generate_task_type=GenerateStreamlitShowcaseApp,
            app_output_name="streamlit_app",
        )
