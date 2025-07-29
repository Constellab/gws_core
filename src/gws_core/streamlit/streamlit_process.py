
from typing import List

from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_service import (AppNginxRedirectServiceInfo,
                                             AppNginxServiceInfo)
from gws_core.apps.app_process import AppProcess, AppProcessStartResult
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_plugin import StreamlitPlugin


class StreamlitProcess(AppProcess):
    """Object representing a streamlit process, one instance of 'streamlit run' command.
    It can manage multiple streamlit apps using the same environment.
    """

    port: int = None

    def __init__(self, port: int, id_: str, env_hash: str = None):
        super().__init__(id_, env_hash)
        self.port = port

    def _start_process(self, app: AppInstance) -> AppProcessStartResult:
        if not isinstance(app, StreamlitApp):
            raise Exception("The app must be a StreamlitApp instance")
        Logger.debug(f"Starting streamlit process for port {self.port}")

        theme = self.get_current_user_theme()

        # Install gws plugin if not already installed
        StreamlitPlugin.install_plugin()

        cmd = ['streamlit', 'run', app.get_main_app_file_path(),
               f'--theme.backgroundColor={theme.background_color}',
               f'--theme.secondaryBackgroundColor={theme.secondary_background_color}',
               f'--theme.textColor={theme.text_color}',
               f'--theme.primaryColor={theme.primary_color}',
               f'--server.port={str(self.port)}',
               # prevent streamlit to open the browser
               '--server.headless=true',
               '--browser.gatherUsageStats=false',
               # Disable XSRF protection to make file uploader work
               # when used in iframe.
               # This is not ideal but it is the only way to make it work
               # It is ok as the ap are secured with a dynamically generated token
               # TODO : check https://github.com/streamlit/streamlit/issues/5793
               '--server.enableXsrfProtection=false'
               #    '--theme.font=Roboto Serif',
               ]

        if app.is_dev_mode():
            cmd += [
                # custom options
                '--',
                # configure a token to secure the app
                f'--dev_mode={app.is_dev_mode()}',
                f'--dev_config_file={app.get_dev_config_file()}',
            ]
        else:
            cmd += [
                # custom options
                '--',
                # configure a token to secure the app
                f'--gws_token={self._token}',
                f'--app_dir={self.get_working_dir()}',
            ]

        shell_proxy = self._get_and_check_shell_proxy(app)

        # Must use the shell_mode=False to retrieve the correct pid to check the number of connections
        process = shell_proxy.run_in_new_thread(cmd, shell_mode=False)

        return AppProcessStartResult(
            process=process,
            services=self._get_nginx_services(),
        )

    def call_health_check(self) -> bool:
        try:
            ExternalApiService.get(f"http://localhost:{self.port}/healthz", raise_exception_if_error=True)
        except Exception:
            return False

        return True

    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""
        return self.port == port

    def _get_nginx_services(self) -> List[AppNginxServiceInfo]:
        if Settings.is_local_env():
            return []

        service = AppNginxRedirectServiceInfo(
            source_port=self.get_service_source_port(),
            service_id=self.id,
            server_name=self.get_cloud_host_name(),
            destination_port=self.port,
        )

        return [service]

    def _get_front_port(self):
        return self.port
