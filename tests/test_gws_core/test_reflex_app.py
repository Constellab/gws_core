from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.core.utils.settings import Settings
from gws_core.impl.apps.reflex_showcase.generate_reflex_showcase_app import (
    GenerateReflexShowcaseApp,
)
from gws_core.impl.shell.shell_proxy import ShellProxy
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

    def test_custom_subdomain_host_name(self):
        app = ReflexApp("resource-model-id", "app", ShellProxy())
        app.set_custom_subdomain("app-hello-world")
        process = ReflexProcess(3000, 8000, app)

        if Settings.is_local_or_desktop_env():
            expected = "app-hello-world.localhost"
            expected_back = "app-hello-world-back.localhost"
        else:
            sub_domain = Settings.get_app_sub_domain()
            virtual_host = Settings.get_virtual_host()
            expected = f"{sub_domain}-app-hello-world.{virtual_host}"
            expected_back = f"{sub_domain}-app-hello-world-back.{virtual_host}"

        self.assertEqual(process.get_host_name(), expected)
        # the reflex backend host keeps the custom subdomain and appends the -back suffix
        self.assertEqual(process.get_host_name("-back"), expected_back)
