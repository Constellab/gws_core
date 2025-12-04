import os
import sys
import time

from gws_core.apps.app_dto import AppProcessStatus
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_service import (
    AppNginxRedirectServiceInfo,
    AppNginxReflexFrontServerServiceInfo,
    AppNginxServiceInfo,
)
from gws_core.apps.app_process import AppProcess, AppProcessStartResult
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.space.space_service import SpaceService


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

    # Cache for reflex access token (class variables for shared caching)
    _cached_access_token: str | None = None
    _cache_timestamp: float | None = None
    _cache_duration_seconds: int = 3600  # 1 hour

    def __init__(self, front_port: int, back_port: int, id_: str, env_hash: str):
        super().__init__(id_, env_hash)
        self.front_port = front_port
        self.back_port = back_port

    def _start_process(self, app: AppInstance) -> AppProcessStartResult:
        if not isinstance(app, ReflexApp):
            raise Exception("The app must be a ReflexApp instance")
        Logger.debug(
            f"Starting reflex process for front port {self.front_port} and back port {self.back_port}"
        )

        shell_proxy = self._get_and_check_shell_proxy(app)
        shell_proxy.working_dir = app.get_app_folder()

        if app.is_dev_mode():
            return self._start_dev_process(app, shell_proxy)
        else:
            return self._start_prod_process(app, shell_proxy)

    def _start_dev_process(
        self, app: AppInstance, shell_proxy: ShellProxy
    ) -> AppProcessStartResult:
        """Start reflex in dev mode with standard 'reflex run' command"""
        cmd = [
            "reflex",
            "run",
            f"--frontend-port={self.front_port}",
            f"--backend-port={self.back_port}",
            self._get_log_level_option(),
            #    f'--env=prod',
        ]

        env = self._get_base_env(app)
        env["GWS_REFLEX_DEV_MODE"] = "true"

        process = shell_proxy.run_in_new_thread(cmd, shell_mode=False, env=env)
        services = self._get_dev_nginx_services()

        return AppProcessStartResult(
            process=process,
            services=services,
        )

    def _get_dev_nginx_services(self) -> list[AppNginxServiceInfo]:
        services: list[AppNginxServiceInfo] = []

        # When dev mode is activated, both front and back are served by the same process
        # so we use a redirect service for the front
        services.append(
            AppNginxRedirectServiceInfo(
                service_id=self.id + "-front",
                source_port=self.get_service_source_port(),
                server_name=self.get_host_name(),
                destination_port=self.front_port,
                # Use localhost host header to avoid issues with some frontend frameworks
                use_localhost_host_header=True,
            )
        )

        services.append(self._get_cloud_back_nginx_services())

        return services

    def _start_prod_process(self, app: ReflexApp, shell_proxy: ShellProxy) -> AppProcessStartResult:
        """Start reflex in prod mode: build frontend (served via nginx), run backend-only"""
        env = self._get_base_env(app)
        env["GWS_REFLEX_TOKEN"] = self._token

        # Build frontend
        front_build_path = self._build_frontend(shell_proxy, env, app)

        # Start backend-only
        backend_cmd = [
            "reflex",
            "run",
            f"--backend-port={self.back_port}",
            "--backend-only",
            self._get_log_level_option(),
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
            os.path.abspath(os.path.dirname(__file__)), ReflexProcess.REFLEX_MODULES_PATH
        )
        if not os.path.exists(reflex_modules_path):
            raise Exception(f"Reflex modules not found at {reflex_modules_path}")

        gws_core_path = os.path.dirname(sys.modules["gws_core"].__path__[0])
        theme = self.get_current_user_theme()

        python_path = reflex_modules_path

        # for non virtual env apps, add gws_core to python path
        if not app.is_virtual_env_app():
            python_path += ":" + gws_core_path

        env_dict = {
            # define python path to include gws_reflex_base and gws_reflex_main and gws_core
            "PYTHONPATH": python_path,
            "GWS_REFLEX_APP_ID": app.resource_model_id,
            "GWS_REFLEX_VIRTUAL_ENV": str(app.is_virtual_env_app()),
            "GWS_REFLEX_API_URL": self.get_back_host_url(),
            "GWS_THEME": theme.theme,
            "GWS_REFLEX_APP_CONFIG_DIR_PATH": self.get_working_dir(),
            "GWS_REFLEX_TEST_ENV": str(Settings.get_instance().is_test),
        }

        # Get access token based on whether this is an enterprise app
        access_token: str | None = None  # Default token
        if isinstance(app, ReflexApp) and app.is_enterprise():
            access_token = self._get_cached_reflex_access_token()
            env_dict["REFLEX_ACCESS_TOKEN"] = access_token

        return env_dict

    def _build_frontend(self, shell_proxy: ShellProxy, env: dict, app: ReflexApp) -> str:
        """Build the frontend for production"""

        front_build_path = app.get_front_build_path_if_exists()

        if front_build_path:
            Logger.info("Frontend is already built, skipping build.")
            return front_build_path

        # delete the cache before building because it seems to be used by reflex build
        # so if the cache is corrupted or on old version, the build may fail
        app.clear_app_cache()

        self.set_status(AppProcessStatus.STARTING, "Building app (it may take a while)...")
        app_build_folder = app.get_front_app_build_folder()
        if not app_build_folder or not app_build_folder.exists():
            raise Exception(f"Destination folder {app_build_folder} does not exist.")

        build_cmd = [
            "reflex",
            "export",
            "--env=prod",
            "--frontend-only",
            "--zip-dest-dir",
            app_build_folder.path,
            "--no-ssr",
        ]

        zip_file_path = os.path.join(app_build_folder.path, ReflexProcess.ZIP_FILE_NAME)
        FileHelper.delete_file(zip_file_path)

        # Log in debug the command to build manually the app
        env_str_cmd = " ".join(f"{key}={value}" for key, value in env.items())
        Logger.debug(f"Command to build frontend: {env_str_cmd} {' '.join(build_cmd)}")

        result = shell_proxy.run(build_cmd, env=env, dispatch_stderr=True, dispatch_stdout=True)
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

    def _get_prod_nginx_services(self, front_build_folder: str) -> list[AppNginxServiceInfo]:
        services: list[AppNginxServiceInfo] = []

        # In prod mode, we serve the front from the build folder
        services.append(
            AppNginxReflexFrontServerServiceInfo(
                service_id=self.id + "-front",
                source_port=self.get_service_source_port(),
                server_name=self.get_host_name(),
                front_folder_path=front_build_folder,
            )
        )

        # the back is always served by a redirect service
        services.append(self._get_cloud_back_nginx_services())

        return services

    def _get_cloud_back_nginx_services(self) -> AppNginxServiceInfo:
        # the back is always served by a redirect service
        return AppNginxRedirectServiceInfo(
            service_id=self.id + "-back",
            source_port=self.get_service_source_port(),
            server_name=self.get_host_name("-back"),
            destination_port=self.back_port,
        )

    def get_back_host_url(self) -> str:
        return self.get_host_url("-back")

    def call_health_check(self) -> bool:
        # health check for both front and back
        try:
            ExternalApiService.get(
                f"http://localhost:{self.back_port}/ping", raise_exception_if_error=True
            )
        except Exception:
            return False

        try:
            # Check the front via Nginx using server_name routing so it works inside container
            # Otherwise this does not work on prod mode with nginx serving the front
            source_port = self.get_service_source_port()
            host_name = self.get_host_name()
            ExternalApiService.get(
                f"http://127.0.0.1:{source_port}",
                headers={"Host": host_name},
                raise_exception_if_error=True,
            )
        except Exception:
            return False

        return True

    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""
        return self.front_port == port or self.back_port == port

    def _get_log_level_option(self) -> str:
        return f"--loglevel={Logger.get_instance().level.lower()}"

    @classmethod
    def _get_cached_reflex_access_token(cls) -> str:
        """Get cached reflex access token if valid, otherwise retrieve and cache new one"""
        reflex_access_token = Settings.get_reflex_access_token()
        if reflex_access_token:
            return reflex_access_token

        current_time = time.time()

        # Check if cache is still valid
        if (
            cls._cached_access_token is not None
            and cls._cache_timestamp is not None
            and current_time - cls._cache_timestamp < cls._cache_duration_seconds
        ):
            return cls._cached_access_token

        # Cache is invalid, retrieve new token
        space_service = SpaceService.get_instance()
        new_token = space_service.get_reflex_access_token()

        # Update cache
        cls._cached_access_token = new_token
        cls._cache_timestamp = current_time

        return new_token
