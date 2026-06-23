from gws_core.apps.app_process import AppProcess
from gws_core.apps.streamlit.streamlit_app import StreamlitApp
from gws_core.apps.streamlit.streamlit_process import StreamlitProcess
from gws_core.apps.streamlit.streamlit_resource import StreamlitResource
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.utils.settings import Settings
from gws_core.impl.apps.streamlit_showcase.generate_streamlit_showcase_app import (
    GenerateStreamlitShowcaseApp,
)
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
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

    def _build_process_with_subdomain(self, subdomain: str | None) -> StreamlitProcess:
        """Build a StreamlitProcess (without starting it) carrying the given custom subdomain."""
        app = StreamlitApp("resource-model-id", "app", ShellProxy())
        app.set_custom_subdomain(subdomain)
        return StreamlitProcess(8501, app)

    def _expected_host(self, host_name: str, suffix: str = "") -> str:
        if Settings.is_local_or_desktop_env():
            return f"{host_name}{suffix}.localhost"
        sub_domain = Settings.get_app_sub_domain()
        virtual_host = Settings.get_virtual_host()
        return f"{sub_domain}-{host_name}{suffix}.{virtual_host}"

    def test_custom_subdomain_is_a_front_alias(self):
        """The canonical host stays id-based; the custom host is added as a front alias."""
        process = self._build_process_with_subdomain("app-hello-world")

        # canonical host is unchanged (id-based)
        self.assertEqual(process.get_host_name(), self._expected_host("resource-model-id"))
        # the custom host is exposed separately
        self.assertEqual(
            process.get_custom_host_name(), self._expected_host("app-hello-world")
        )
        # the front nginx server_name lists both the id host and the custom alias
        front_service = process._get_nginx_services()[0]
        self.assertEqual(
            front_service.server_name,
            [self._expected_host("resource-model-id"), self._expected_host("app-hello-world")],
        )

    def test_default_host_name_unchanged(self):
        """With no custom subdomain, the front answers only on the resource model id host."""
        process = self._build_process_with_subdomain(None)

        self.assertEqual(process.get_host_name(), self._expected_host("resource-model-id"))
        self.assertIsNone(process.get_custom_host_name())
        front_service = process._get_nginx_services()[0]
        self.assertEqual(
            front_service.server_name, [self._expected_host("resource-model-id")]
        )

    def test_dev_mode_ignores_custom_subdomain(self):
        app = StreamlitApp("resource-model-id", "app", ShellProxy())
        app.set_custom_subdomain("app-hello-world")
        app.set_dev_mode()
        process = StreamlitProcess(8501, app)

        self.assertEqual(
            process.get_host_name(), self._expected_host(AppProcess.DEV_MODE_APP_ID)
        )
        # the custom subdomain is ignored in dev mode
        self.assertIsNone(process.get_custom_host_name())

    def test_custom_subdomain_validation(self):
        # use a subdomain that no other test persists, so the uniqueness check does not interfere
        resource = StreamlitResource()

        # uppercase is normalized to lowercase (valid)
        resource.set_custom_subdomain("App-Valid-Subdomain")
        self.assertEqual(resource.get_custom_subdomain(), "app-valid-subdomain")

        # invalid values raise
        for invalid in ["-leading-dash", "trailing-dash-", "has space", "under_score", "a" * 64]:
            with self.assertRaises(BadRequestException):
                resource.set_custom_subdomain(invalid)

        # reserved value raises
        with self.assertRaises(BadRequestException):
            resource.set_custom_subdomain(AppProcess.DEV_MODE_APP_ID)

        # falsy clears the subdomain
        resource.set_custom_subdomain("app-valid-subdomain")
        resource.set_custom_subdomain("")
        self.assertIsNone(resource.get_custom_subdomain())

    def test_custom_subdomain_uniqueness(self):
        first = StreamlitResource()
        first.set_streamlit_code("import streamlit as st")
        first.set_custom_subdomain("app-hello-world")
        first_model = ResourceModel.save_from_resource(first, origin=ResourceOrigin.UPLOADED)

        second = StreamlitResource()
        second.set_streamlit_code("import streamlit as st")

        # using the same subdomain on another app raises
        with self.assertRaises(BadRequestException):
            second.set_custom_subdomain("app-hello-world")

        # a different subdomain is accepted
        second.set_custom_subdomain("app-other")
        self.assertEqual(second.get_custom_subdomain(), "app-other")

        # re-setting the same value on the original (persisted) app, which already owns the
        # subdomain, is allowed (the uniqueness check skips the app itself)
        reloaded = first_model.get_resource()
        reloaded.set_custom_subdomain("app-hello-world")
        self.assertEqual(reloaded.get_custom_subdomain(), "app-hello-world")
