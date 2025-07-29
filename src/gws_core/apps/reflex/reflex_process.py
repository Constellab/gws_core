

import os
import sys
from typing import List

from gws_core.apps.app_dto import AppProcessStatus
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_service import (
    AppNginxRedirectServiceInfo, AppNginxReflexFrontServerServiceInfo,
    AppNginxServiceInfo)
from gws_core.apps.app_process import AppProcess, AppProcessStartResult
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.shell_proxy import ShellProxy


class ReflexProcess(AppProcess):
    """Object representing a running Reflex app process.
    This process runs the front and back of a Reflex app.
    In dev mode: runs 'reflex run'.
    In prod mode: builds frontend (served by nginx) and runs backend-only.

    There is 1 ReflexProcess per app. If the same reflex app
    is runned multiple times, it will use the different processes.
    In prod the front build folder is stored in resource path.
    """

    front_port: int = None
    back_port: int = None

    # timeout in second to wait for the main app to start
    # increase it to 90 to allow the app to start as it compiles the front and back
    START_APP_TIMEOUT = 90

    REFLEX_MODULES_PATH = "_gws_reflex"
    ZIP_FILE_NAME = "frontend.zip"
    INDEX_HTML_FILE = "index.html"

    _front_app_build_folder: str = None

    def __init__(self,
                 front_port: int,
                 back_port: int,
                 id_: str,
                 env_hash: str):
        super().__init__(id_, env_hash)
        self.front_port = front_port
        self.back_port = back_port

    def _start_process(self, app: AppInstance) -> AppProcessStartResult:
        if not isinstance(app, ReflexApp):
            raise Exception("The app must be a ReflexApp instance")
        Logger.debug(f"Starting reflex process for front port {self.front_port} and back port {self.back_port}")

        shell_proxy = self._get_and_check_shell_proxy(app)
        shell_proxy.working_dir = app.get_app_folder()

        if app.is_dev_mode():
            return self._start_dev_process(app, shell_proxy)
        else:
            return self._start_prod_process(app, shell_proxy)

    def _start_dev_process(self, app: AppInstance, shell_proxy: ShellProxy) -> AppProcessStartResult:
        """Start reflex in dev mode with standard 'reflex run' command"""
        cmd = ['reflex', 'run',
               f'--frontend-port={self.front_port}',
               f'--backend-port={self.back_port}',
               #    f'--env=prod',
               ]

        env = self._get_base_env(app)
        env['GWS_REFLEX_DEV_MODE'] = 'true'
        env['GWS_REFLEX_DEV_CONFIG_FILE_PATH'] = app.get_dev_config_file()

        process = shell_proxy.run_in_new_thread(cmd, shell_mode=False, env=env)
        services = self._get_dev_nginx_services()

        return AppProcessStartResult(
            process=process,
            services=services,
        )

    def _get_dev_nginx_services(self) -> List[AppNginxServiceInfo]:
        if Settings.is_local_env():
            # In local environment, we don't need nginx services
            if self.is_dev_mode:
                return []

        services: List[AppNginxServiceInfo] = []

        # When dev mode is activated, both front and back are served by the same process
        # so we use a redirect service for the front
        services.append(AppNginxRedirectServiceInfo(
            service_id=self.id + '-front',
            source_port=self.get_service_source_port(),
            server_name=self.get_cloud_host_name(),
            destination_port=self.front_port,
        ))

        services.append(self._get_cloud_back_nginx_services())

        return services

    def _start_prod_process(self, app: ReflexApp, shell_proxy: ShellProxy) -> AppProcessStartResult:
        """Start reflex in prod mode: build frontend (served via nginx), run backend-only"""
        env = self._get_base_env(app)
        env['GWS_REFLEX_TOKEN'] = self._token
        env['GWS_REFLEX_APP_CONFIG_DIR_PATH'] = self.get_working_dir()

        # Build frontend
        front_build_path = self._build_frontend(shell_proxy, env, app)

        # Start backend-only
        backend_cmd = ['reflex', 'run',
                       f'--backend-port={self.back_port}',
                       '--backend-only',
                       # For now disabled prod for backend because it
                       # files with gws_core imports
                       #    '--env=prod'
                       ]

        process = shell_proxy.run_in_new_thread(backend_cmd, shell_mode=False, env=env)

        services = self._get_prod_nginx_services(front_build_path)

        return AppProcessStartResult(
            process=process,
            services=services,
        )

    def _get_base_env(self, app: AppInstance) -> dict:
        """Get base environment variables for reflex processes"""
        reflex_modules_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            ReflexProcess.REFLEX_MODULES_PATH
        )
        if not os.path.exists(reflex_modules_path):
            raise Exception(f"Reflex modules not found at {reflex_modules_path}")

        gws_core_path = os.path.dirname(sys.modules['gws_core'].__path__[0])
        theme = self.get_current_user_theme()

        return {
            'GWS_REFLEX_APP_ID': app.resource_model_id,
            'GWS_REFLEX_MODULES_PATH': reflex_modules_path,
            'GWS_REFLEX_VIRTUAL_ENV': str(app.is_virtual_env_app()),
            'GWS_REFLEX_GWS_CORE_PATH': gws_core_path,
            'GWS_REFLEX_API_URL': self.get_back_host_url(),
            'GWS_THEME': theme.theme,
        }

    def _build_frontend(self, shell_proxy: ShellProxy, env: dict, app: ReflexApp) -> str:
        """Build the frontend for production"""

        front_build_path = app.get_front_build_path_if_exists()

        if front_build_path:
            Logger.info("Frontend is already built, skipping build.")
            return front_build_path

        self.set_status(AppProcessStatus.STARTING, "Building app (it may take a while)...")
        app_build_folder = app.get_front_app_build_folder()
        if not app_build_folder.exists():
            raise Exception(f"Destination folder {app_build_folder} does not exist.")

        build_cmd = ['reflex', 'export', '--env=prod', '--frontend-only', '--zip-dest-dir', app_build_folder.path]

        zip_file_path = os.path.join(app_build_folder.path, ReflexProcess.ZIP_FILE_NAME)
        FileHelper.delete_file(zip_file_path)

        result = shell_proxy.run(build_cmd, env=env)
        if result != 0:
            raise Exception(f"Failed to build REFLEX frontend app {app.get_app_folder()}.")

        # Unzip the build  and delete the zip file
        if not FileHelper.exists_on_os(zip_file_path):
            raise Exception(f"Frontend build zip file {zip_file_path} does not exist after build.")

        ZipCompress.decompress(zip_file_path, app_build_folder.path)
        FileHelper.delete_file(zip_file_path)

        # Check the build folder
        # path of the build generated by the command
        index_html_file = os.path.join(app_build_folder.path, ReflexProcess.INDEX_HTML_FILE)
        if not os.path.exists(index_html_file):
            raise Exception(f"Index html file {index_html_file} does not exist after build.")

        # store the build info
        app.update_front_build_info()

        Logger.info("Frontend built successfully")
        return app_build_folder.path

    def _get_prod_nginx_services(self, front_build_folder: str) -> List[AppNginxServiceInfo]:
        # In local prod, we need to serve the front from the build folder
        if Settings.is_local_env():
            Logger.info(f"Reflex frontend is served by nginx in port {self.front_port}." +
                        " In local environment you must forward this port manually.")
            return [AppNginxReflexFrontServerServiceInfo(
                service_id=self.id,
                    source_port=self.front_port,
                    server_name='localhost',
                    front_folder_path=front_build_folder,
                    )]

        services: List[AppNginxServiceInfo] = []

        # In prod mode, we serve the front from the build folder
        services.append(AppNginxReflexFrontServerServiceInfo(
            service_id=self.id + '-front',
            source_port=self.get_service_source_port(),
            server_name=self.get_cloud_host_name(),
            front_folder_path=front_build_folder,
        ))

        # the back is always served by a redirect service
        services.append(self._get_cloud_back_nginx_services())

        return services

    def _get_cloud_back_nginx_services(self) -> AppNginxServiceInfo:
        # the back is always served by a redirect service
        return AppNginxRedirectServiceInfo(
            service_id=self.id + '-back',
            source_port=self.get_service_source_port(),
            server_name=self.get_cloud_host_name('-back'),
            destination_port=self.back_port,
        )

    def get_back_host_url(self) -> str:
        if Settings.is_cloud_env():
            return f"https://{self.get_cloud_host_name('-back')}"
        else:
            return f"http://localhost:{self.back_port}"

    def call_health_check(self) -> bool:
        # health check for both front and back
        try:
            ExternalApiService.get(self.get_back_host_url() + '/ping',
                                   raise_exception_if_error=True)
        except Exception:
            return False

        try:
            ExternalApiService.get(self.get_host_url(),
                                   raise_exception_if_error=True)
        except Exception:
            return False

        return True

    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""
        return self.front_port == port or self.back_port == port

    def _get_front_port(self):
        return self.front_port
