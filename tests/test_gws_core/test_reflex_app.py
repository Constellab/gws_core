from gws_core.impl.apps.reflex_showcase.generate_reflex_showcase_app import (
    GenerateReflexShowcaseApp,
)
from gws_core.impl.table.table import Table
from gws_core.test.app_tester import AppTester
from gws_core.test.base_test_case import BaseTestCase
from pandas import DataFrame


# test_reflex_app
class TestReflexApp(BaseTestCase):
    def test_reflex_resource(self):
        df = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        table = Table(df)

        AppTester.test_app_from_task(
            test_case=self,
            generate_task_type=GenerateReflexShowcaseApp,
            app_output_name="reflex_app",
            input_resources={"resource": table},
        )
