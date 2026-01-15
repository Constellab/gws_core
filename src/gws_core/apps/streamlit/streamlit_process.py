import os

from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_service import AppNginxRedirectServiceInfo, AppNginxServiceInfo
from gws_core.apps.app_process import AppProcess, AppProcessStartResult
from gws_core.apps.streamlit.streamlit_app import StreamlitApp
from gws_core.apps.streamlit.streamlit_plugin import StreamlitPlugin
from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.logger import Logger


class StreamlitProcess(AppProcess):
    """Object representing a streamlit process, one instance of 'streamlit run' command.
    It can manage multiple streamlit apps using the same environment.
    """

    port: int

    STREAMLIT_MODULES_PATH = "_gws_streamlit"

    def __init__(self, port: int, app: AppInstance):
        super().__init__(app)
        self.port = port

    def _start_process(self, app: AppInstance) -> AppProcessStartResult:
        if not isinstance(app, StreamlitApp):
            raise Exception("The app must be a StreamlitApp instance")
        Logger.debug(f"Starting streamlit process for port {self.port}")

        theme = self.get_current_user_theme()

        # build code if needed
        app.build_code(self.get_working_dir())

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
        ]

        # File watching configuration
        if app.is_dev_mode():
            # In dev mode, keep file watching but exclude gws_core for performance
            gws_core_path = BrickHelper.get_brick_info_and_check(
                BrickHelper.GWS_CORE
            ).get_python_module_path()
            options.append(f"--server.folderWatchBlacklist={gws_core_path}")
        else:
            # In production, disable file watching completely for better performance
            options.append("--server.fileWatcherType=none")

        env = self._get_base_env(app)

        if app.is_dev_mode():
            # Run user's main.py directly
            cmd = ["run", app.get_user_main_file_path()] + options

            # Adjust command based on debugger mode
            if app.enable_debugger:
                # Run streamlit through python to keep the debugger enabled
                # So streamlit app is debuggable
                cmd = ["python3", self._get_streamlit_package_path()] + cmd
                debug_msg = f"Running streamlit in dev mode with debugger enabled: {' '.join(cmd)}"
            else:
                # When debugger not active (running from CLI) we can use the normal streamlit command
                # If we use the python command, there is a streamlit error
                cmd = ["streamlit"] + cmd
                debug_msg = f"Running streamlit in dev mode: {' '.join(cmd)}"

            Logger.debug(debug_msg)
            shell_proxy = self._get_and_check_shell_proxy(app)
            process = shell_proxy.run_in_new_thread(cmd, shell_mode=False, env=env)
        else:
            shell_proxy = self._get_and_check_shell_proxy(app)
            # Run user's main.py directly
            cmd = ["streamlit", "run", app.get_user_main_file_path()] + options
            process = shell_proxy.run_in_new_thread(cmd, shell_mode=False, env=env)

        return AppProcessStartResult(
            process=process,
            services=self._get_nginx_services(),
        )

    def _get_base_env(self, app: StreamlitApp) -> dict:
        """Get base environment variables for Streamlit processes (v2 architecture)."""
        # Get path to _gws_streamlit modules
        streamlit_modules_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), StreamlitProcess.STREAMLIT_MODULES_PATH
        )
        if not os.path.exists(streamlit_modules_path):
            raise Exception(f"Streamlit modules not found at {streamlit_modules_path}")

        # Get gws_core path
        brick_info = BrickHelper.get_brick_info_and_check(BrickHelper.GWS_CORE)

        # Get app directory path for relative imports
        app_dir_path = os.path.abspath(app.get_app_folder_path())
        parent_dir = os.path.dirname(app_dir_path)

        # Build PYTHONPATH:
        # 1. Add _gws_streamlit modules
        # 2. Add parent directory of app (enables relative imports like: from .pages import ...)
        # 3. Add app directory itself (enables imports from within app)
        python_path = streamlit_modules_path + ":" + parent_dir + ":" + app_dir_path

        # For non-virtual env apps, add gws_core to python path
        if not app.is_virtual_env_app():
            python_path += ":" + brick_info.get_python_module_path()

        env_dict = self._get_common_env_variables()
        env_dict["PYTHONPATH"] = python_path

        return env_dict

    def _get_streamlit_package_path(self) -> str:
        import streamlit

        return os.path.dirname(streamlit.__file__)

    def call_health_check(self) -> bool:
        try:
            ExternalApiService.get(
                f"http://localhost:{self.port}/healthz", raise_exception_if_error=True
            )
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
                service_id=self.get_id() + "-streamlit",
                server_name=self.get_host_name(),
                destination_port=self.port,
            )
        ]
