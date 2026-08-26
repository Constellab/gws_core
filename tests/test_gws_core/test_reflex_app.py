from gws_core.apps.app_nginx_service import AppNginxRedirectServiceInfo
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

    def _expected_host(self, host_name: str, suffix: str = "") -> str:
        if Settings.is_local_or_desktop_env():
            return f"{host_name}{suffix}.localhost"
        sub_domain = Settings.get_app_sub_domain()
        virtual_host = Settings.get_virtual_host()
        return f"{sub_domain}-{host_name}{suffix}.{virtual_host}"

    def test_custom_subdomain_is_front_only_alias(self):
        app = ReflexApp("resource-model-id", "app", ShellProxy())
        app.set_custom_subdomain("app-hello-world")
        process = ReflexProcess(3000, 8000, app)

        # canonical front/back hosts stay id-based
        self.assertEqual(process.get_host_name(), self._expected_host("resource-model-id"))
        self.assertEqual(
            process.get_host_name("-back"), self._expected_host("resource-model-id", "-back")
        )
        # the custom host is the front alias only
        self.assertEqual(
            process.get_custom_host_name(), self._expected_host("app-hello-world")
        )

        # front nginx block answers on both the id host and the custom alias
        self.assertEqual(
            process.get_front_server_names(),
            [self._expected_host("resource-model-id"), self._expected_host("app-hello-world")],
        )

        # the backend service host is id-only, but its CORS allow-list includes the custom front
        back_service = process._get_cloud_back_nginx_services()
        assert isinstance(back_service, AppNginxRedirectServiceInfo)
        self.assertEqual(
            back_service.server_name, self._expected_host("resource-model-id", "-back")
        )
        self.assertIn(process.get_custom_host_url(), back_service.allowed_origins)
        self.assertIn(process.get_host_url(), back_service.allowed_origins)

    def test_default_host_name_unchanged(self):
        app = ReflexApp("resource-model-id", "app", ShellProxy())
        process = ReflexProcess(3000, 8000, app)

        self.assertEqual(process.get_host_name(), self._expected_host("resource-model-id"))
        self.assertIsNone(process.get_custom_host_name())
        self.assertEqual(
            process.get_front_server_names(), [self._expected_host("resource-model-id")]
        )
