import os

from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_service import AppNginxRedirectServiceInfo, AppNginxServiceInfo
from gws_core.apps.app_process import AppProcess, AppProcessStartResult
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.logger import Logger
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_plugin import StreamlitPlugin


class StreamlitProcess(AppProcess):
    """Object representing a streamlit process, one instance of 'streamlit run' command.
    It can manage multiple streamlit apps using the same environment.
    """

    port: int

    def __init__(self, port: int, id_: str, env_hash: str | None = None):
        super().__init__(id_, env_hash)
        self.port = port

    def _start_process(self, app: AppInstance) -> AppProcessStartResult:
        if not isinstance(app, StreamlitApp):
            raise Exception("The app must be a StreamlitApp instance")
        Logger.debug(f"Starting streamlit process for port {self.port}")

        theme = self.get_current_user_theme()

        # Install gws plugin if not already installed
        StreamlitPlugin().install_package()

        process: SysProc

        options = [
            f"--server.port={str(self.port)}",
            f"--theme.backgroundColor={theme.background_color}",
            f"--theme.secondaryBackgroundColor={theme.secondary_background_color}",
            f"--theme.textColor={theme.text_color}",
            f"--theme.primaryColor={theme.primary_color}",
            # prevent streamlit to open the browser
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            # Disable XSRF protection to make file uploader work
            # when used in iframe.
            # This is not ideal but it is the only way to make it work
            # It is ok as the ap are secured with a dynamically generated token
            # TODO : check https://github.com/streamlit/streamlit/issues/5793
            "--server.enableXsrfProtection=false",
            # custom options
            "--",
            f"--app_dir={self.get_working_dir()}",
        ]

        if app.is_dev_mode():
            cmd = ["run", app.get_main_app_file_path()] + options + [f"--dev_mode={app.is_dev_mode()}"]

            if app.enable_debugger:
                # Run streamlit through python to keep the debugger enable
                # So streamlit app is debuggable
                cmd = ["python3", self._get_streamlit_package_path()] + cmd
                Logger.debug(f"Running streamlit in dev mode with debugger enabled: {' '.join(cmd)}")
                process = SysProc.popen(cmd)
            else:
                # when debugger not active (running from CLI) we can use the normal streamlit command
                # if we use the python command, there is a streamlit error
                cmd = ["streamlit"] + cmd
                shell_proxy = self._get_and_check_shell_proxy(app)
                Logger.debug(f"Running streamlit in dev mode: {' '.join(cmd)}")
                process = shell_proxy.run_in_new_thread(cmd, shell_mode=False)
        else:
            shell_proxy = self._get_and_check_shell_proxy(app)
            cmd = ["streamlit", "run", app.get_main_app_file_path()] + options + [f"--gws_token={self._token}"]
            process = shell_proxy.run_in_new_thread(cmd, shell_mode=False)

        return AppProcessStartResult(
            process=process,
            services=self._get_nginx_services(),
        )

    def _get_streamlit_package_path(self) -> str:
        import streamlit

        return os.path.dirname(streamlit.__file__)

    def call_health_check(self) -> bool:
        try:
            ExternalApiService.get(f"http://localhost:{self.port}/healthz", raise_exception_if_error=True)
        except Exception:
            return False

        return True

    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""
        return self.port == port

    def _get_nginx_services(self) -> list[AppNginxServiceInfo]:
        return [
            AppNginxRedirectServiceInfo(
                source_port=self.get_service_source_port(),
                service_id=self.id,
                server_name=self.get_host_name(),
                destination_port=self.port,
            )
        ]
