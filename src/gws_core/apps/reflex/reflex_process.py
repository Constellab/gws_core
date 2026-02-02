import glob
import os
import shutil
import tempfile
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
from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.execution_context import ExecutionContext
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

    front_port: int
    back_port: int

    # timeout in second to wait for the main app to start
    # increase it to 90 to allow the app to start as it compiles the front and back
    START_APP_TIMEOUT = 90

    REFLEX_MODULES_PATH = "_gws_reflex"
    ZIP_FILE_NAME = "frontend.zip"
    INDEX_HTML_FILE = "index.html"
    # Placeholder used during build to allow runtime api_url replacement
    # This placeholder is replaced with the actual api_url when starting each instance
    API_URL_PLACEHOLDER = "http://gws-api-url-placeholder.localhost:8510"

    _front_app_build_folder: str | None = None

    # Cache for reflex access token (class variables for shared caching)
    _cached_access_token: str | None = None
    _cache_timestamp: float | None = None
    _cache_duration_seconds: int = 3600  # 1 hour

    def __init__(self, front_port: int, back_port: int, app: AppInstance):
        super().__init__(app)
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
                service_id=self.get_id() + "-front",
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
        # For build, use placeholder so we can patch it per-instance
        build_env = self._get_base_env(app, use_placeholder_api_url=True)

        # Build frontend (uses placeholder api_url)
        front_build_path = self._build_frontend(shell_proxy, build_env, app)

        # Create a patched copy with the real api_url for this instance
        actual_api_url = self.get_back_host_url()
        patched_front_path = self._create_patched_frontend_copy(front_build_path, actual_api_url)

        # For backend runtime, use the real api_url
        runtime_env = self._get_base_env(app, use_placeholder_api_url=False)

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

        process = shell_proxy.run_in_new_thread(backend_cmd, shell_mode=False, env=runtime_env)

        # Use the patched frontend folder for nginx
        services = self._get_prod_nginx_services(patched_front_path)

        return AppProcessStartResult(
            process=process,
            services=services,
        )

    def _get_base_env(self, app: AppInstance, use_placeholder_api_url: bool = False) -> dict:
        """Get base environment variables for reflex processes.

        :param app: The app instance
        :param use_placeholder_api_url: If True, use a placeholder for api_url (for building).
                                        If False, use the actual api_url (for runtime).
        """
        reflex_modules_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), ReflexProcess.REFLEX_MODULES_PATH
        )
        if not os.path.exists(reflex_modules_path):
            raise Exception(f"Reflex modules not found at {reflex_modules_path}")

        brick_info = BrickHelper.get_brick_info_and_check(BrickHelper.GWS_CORE)
        theme = self.get_current_user_theme()

        python_path = reflex_modules_path

        # for non virtual env apps, add gws_core to python path
        if not app.is_virtual_env_app():
            python_path += ":" + brick_info.get_python_module_path()

        env_dict = self._get_common_env_variables(ExecutionContext.REFLEX)

        # define python path to include gws_reflex_base and gws_reflex_main and gws_core
        env_dict["PYTHONPATH"] = python_path

        # Use placeholder during build so we can patch per-instance at runtime
        if use_placeholder_api_url:
            env_dict["GWS_REFLEX_API_URL"] = ReflexProcess.API_URL_PLACEHOLDER
        else:
            env_dict["GWS_REFLEX_API_URL"] = self.get_back_host_url()

        env_dict["GWS_THEME"] = theme.theme

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

    def _create_patched_frontend_copy(self, source_build_folder: str, api_url: str) -> str:
        """Create a copy of the frontend build with the api_url placeholder replaced.

        This allows multiple instances of the same app to run with different backend URLs.
        The copy is created in a temporary directory that will be cleaned up when the process stops.

        :param source_build_folder: Path to the original build folder
        :param api_url: The actual api_url to use for this instance
        :return: Path to the patched copy
        """
        # Create a unique temp directory for this instance
        patched_folder = tempfile.mkdtemp(prefix=f"reflex_front_{self.get_id()}_")
        self._front_app_build_folder = patched_folder

        Logger.debug(f"Creating patched frontend copy in {patched_folder}")

        # Copy the entire build folder
        shutil.copytree(source_build_folder, patched_folder, dirs_exist_ok=True)

        # Find and patch the reflex-env JS file (contains the api_url)
        # The file is named like: reflex-env-XXXX.js in assets folder
        assets_folder = os.path.join(patched_folder, "client", "assets")
        if os.path.exists(assets_folder):
            env_files = glob.glob(os.path.join(assets_folder, "reflex-env-*.js"))
            for env_file in env_files:
                self._replace_placeholder_in_file(env_file, api_url)

        # Also patch env.json if it exists (for backwards compatibility)
        env_json_path = os.path.join(patched_folder, "env.json")
        if os.path.exists(env_json_path):
            self._replace_placeholder_in_file(env_json_path, api_url)

        Logger.info(f"Patched frontend with api_url: {api_url}")
        return patched_folder

    def _replace_placeholder_in_file(self, file_path: str, api_url: str) -> None:
        """Replace the API_URL_PLACEHOLDER with the actual api_url in a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace the placeholder hostname with the actual api_url hostname
            # The placeholder looks like: http://gws-api-url-placeholder.localhost:8510
            # We need to replace it with the actual URL like: http://uuid-back.localhost:8510
            if ReflexProcess.API_URL_PLACEHOLDER in content:
                new_content = content.replace(ReflexProcess.API_URL_PLACEHOLDER, api_url)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                Logger.debug(f"Patched api_url in {file_path}")
        except Exception as e:
            Logger.warning(f"Failed to patch {file_path}: {e}")

    def _cleanup_patched_frontend(self) -> None:
        """Clean up the temporary patched frontend folder."""
        if self._front_app_build_folder and os.path.exists(self._front_app_build_folder):
            try:
                shutil.rmtree(self._front_app_build_folder)
                Logger.debug(f"Cleaned up patched frontend: {self._front_app_build_folder}")
            except Exception as e:
                Logger.warning(f"Failed to cleanup patched frontend: {e}")
            self._front_app_build_folder = None

    def _get_prod_nginx_services(self, front_build_folder: str) -> list[AppNginxServiceInfo]:
        services: list[AppNginxServiceInfo] = []

        # In prod mode, we serve the front from the build folder
        services.append(
            AppNginxReflexFrontServerServiceInfo(
                service_id=self.get_id() + "-front",
                source_port=self.get_service_source_port(),
                server_name=self.get_host_name(),
                front_folder_path=front_build_folder,
            )
        )

        # the back is always served by a redirect service
        services.append(self._get_cloud_back_nginx_services())

        return services

    def _get_cloud_back_nginx_services(self) -> AppNginxServiceInfo:
        return AppNginxRedirectServiceInfo(
            service_id=self.get_id() + "-back",
            source_port=self.get_service_source_port(),
            server_name=self.get_host_name("-back"),
            destination_port=self.back_port,
            # the back is always served by a redirect service
            # Set allowed_origin to the frontend URL to enable CORS
            allowed_origin=self.get_host_url(),
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

    def stop_process(self) -> None:
        """Kill the process, clean up patched frontend, and stop the app"""
        # Clean up the patched frontend folder before stopping
        self._cleanup_patched_frontend()
        # Call parent's stop_process
        super().stop_process()

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
