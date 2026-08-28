import os
import threading
import time

from gws_core.apps import app_gateway_constants
from gws_core.apps.app_dir_locks import AppDirLocks
from gws_core.apps.app_dto import AppProcessStatus
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_service import (
    AppNginxRedirectServiceInfo,
    AppNginxReflexFrontServerServiceInfo,
    AppNginxServiceInfo,
)
from gws_core.apps.app_process import AppProcess, AppProcessStartResult
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_front_build_cache import ReflexFrontBuildCache
from gws_core.apps.reflex.reflex_plugin import ReflexPlugin
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
    # increase it to 120 to allow the app to start as it compiles the front and back
    START_APP_TIMEOUT = 120

    REFLEX_MODULES_PATH = "_gws_reflex"
    ZIP_FILE_NAME = "frontend.zip"
    INDEX_HTML_FILE = "index.html"

    # Path prefix under which the reflex backend serves its endpoints (same-origin
    # routing). Set via REFLEX_BACKEND_PATH on BOTH the export env (baked into the
    # frontend URLs) and the prod backend runtime env (endpoints + socket.io
    # namespace mounted under it): the socket.io namespace is derived from the URL
    # path on both sides and travels inside the websocket payload, so client and
    # server must agree on it — nginx proxies the prefix through without stripping.
    BACKEND_PATH = "/gws-back"
    # Set to "1" in the reflex export env so gws_reflex state code can avoid baking
    # instance-specific values (app id, auth info) into the compiled bundle.
    BUILD_MODE_ENV_VAR = "GWS_REFLEX_BUILD_MODE"

    _front_app_build_folder: str | None = None

    # Cache for reflex access token (class variables for shared caching)
    _cached_access_token: str | None = None
    _cache_timestamp: float | None = None
    _cache_duration_seconds: int = 3600  # 1 hour
    # serializes the check-then-fetch of the token cache across app start threads
    _token_cache_lock = threading.Lock()

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

        shell_proxy = self._get_and_check_shell_proxy()
        shell_proxy.working_dir = app.get_app_folder()

        if app.is_dev_mode():
            return self._start_dev_process(app, shell_proxy)
        else:
            return self._start_prod_process(app, shell_proxy)

    def _start_dev_process(
        self, app: ReflexApp, shell_proxy: ShellProxy
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

        # Make sure the gws_plugin is materialized in the app folder before reflex
        # imports the components (avoids a download from inside the reflex process)
        ReflexPlugin(app.get_app_folder()).install_package()

        process = shell_proxy.run_in_new_thread(
            cmd, shell_mode=False, env=env, dispatch_stderr=True
        )
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
        env = self._get_base_env(app)

        # Mount the backend endpoints (and the socket.io namespace) under BACKEND_PATH:
        # the frontend bundle bakes its URLs under the same prefix, and the socket.io
        # namespace must match on both sides (it is negotiated inside the websocket
        # payload, nginx cannot rewrite it).
        env["REFLEX_BACKEND_PATH"] = ReflexProcess.BACKEND_PATH

        # Build frontend
        front_build_path = self._build_frontend(shell_proxy, env, app)

        # Ensure the gws_plugin is present in the app folder for the backend workers
        # (no-op version check when the build above just materialized it)
        ReflexPlugin(app.get_app_folder()).install_package()

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

        process = shell_proxy.run_in_new_thread(
            backend_cmd, shell_mode=False, env=env, dispatch_stderr=True
        )

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

        brick_info = BrickHelper.get_brick_info_and_check(BrickHelper.GWS_CORE)

        python_path = reflex_modules_path

        # for non virtual env apps, add gws_core to python path
        if not app.is_virtual_env_app():
            python_path += ":" + brick_info.get_python_module_path()

        env_dict = self._get_common_env_variables(ExecutionContext.REFLEX)

        # define python path to include gws_reflex_base and gws_reflex_main and gws_core
        env_dict["PYTHONPATH"] = python_path
        env_dict["GWS_REFLEX_API_URL"] = self.get_back_host_url()

        # Get access token based on whether this is an enterprise app
        access_token: str | None = None  # Default token
        if isinstance(app, ReflexApp) and app.is_enterprise():
            access_token = self._get_cached_reflex_access_token()
            env_dict["REFLEX_ACCESS_TOKEN"] = access_token

        return env_dict

    def _build_frontend(self, shell_proxy: ShellProxy, env: dict, app: ReflexApp) -> str:
        """Build the frontend for production.

        Builds of the same app folder are serialized: several instances of one app share
        the folder (`.web`, `node_modules`, `assets`), and concurrent `reflex export`
        runs delete each other's state mid-build (missing `node_modules/.bin` binaries,
        `bun install` FileNotFound, corrupted lockfiles). Late arrivals wait, then reuse
        the finished build when their resource already has one.
        """
        with AppDirLocks.get_lock(app.get_app_folder()):
            return self._build_frontend_locked(shell_proxy, env, app)

    def _build_frontend_locked(self, shell_proxy: ShellProxy, env: dict, app: ReflexApp) -> str:
        # Checked inside the lock (double-checked locking): another instance of the same
        # app may have finished this resource's build while this thread was waiting.
        front_build_path = app.get_front_build_path_if_exists()

        if front_build_path:
            Logger.info("Frontend is already built, skipping build.")
            return front_build_path

        app_build_folder = app.get_front_app_build_folder()
        if not app_build_folder or not app_build_folder.exists():
            raise Exception(f"Destination folder {app_build_folder} does not exist.")

        # The bundle is instance-independent (see _get_build_env), so builds of
        # AppConfig apps are shared across instances through a cache: only the first
        # instance runs `reflex export`, the others copy the cached build.
        build_cache = self._get_build_cache(app)
        if build_cache and build_cache.get_cached_build_path():
            Logger.info(
                f"Reusing cached frontend build for app {app.resource_model_id} "
                f"from {build_cache.get_entry_path()}"
            )
            build_cache.copy_into(app_build_folder.path)
            app.update_front_build_info()
            return app_build_folder.path

        # delete the cache before building because it seems to be used by reflex build
        # so if the cache is corrupted or on old version, the build may fail
        app.clear_app_cache()

        # assets/external was just cleared: re-materialize the gws_plugin from the
        # lab-wide immutable store before reflex compiles the assets
        ReflexPlugin(app.get_app_folder()).install_package()

        self.set_status(AppProcessStatus.STARTING, "Building app (it may take a while)...")
        build_started_at = time.time()
        Logger.info(
            f"Frontend build started for app {app.resource_model_id} "
            f"in {app.get_app_folder()}"
        )

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

        build_env = self._get_build_env(env)

        # Log in debug the command to build manually the app
        env_str_cmd = " ".join(f"{key}={value}" for key, value in build_env.items())
        Logger.debug(f"Command to build frontend: {env_str_cmd} {' '.join(build_cmd)}")

        result = shell_proxy.run(
            build_cmd, env=build_env, dispatch_stderr=True, dispatch_stdout=True
        )
        if result != 0:
            Logger.error(
                f"Frontend build failed for app {app.resource_model_id} "
                f"after {time.time() - build_started_at:.0f}s (exit {result})"
            )
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

        # Share the fresh build with other instances of the same app. Skipped when the
        # bundle turns out to contain the builder's instance id (user app baking
        # instance env vars at import time).
        if build_cache:
            build_cache.store_build(
                app_build_folder.path, instance_marker=app.resource_model_id
            )

        Logger.info(
            f"Frontend build finished for app {app.resource_model_id} "
            f"in {time.time() - build_started_at:.0f}s"
        )
        return app_build_folder.path

    def _get_build_cache(self, app: ReflexApp) -> ReflexFrontBuildCache | None:
        """Build cache for this app, or None when not cacheable (static-folder apps
        carry their code per resource, so their builds cannot be shared)."""
        app_config = app.get_app_config()
        if not app_config:
            return None
        return ReflexFrontBuildCache(app_config, ReflexProcess.BACKEND_PATH)

    def _get_build_env(self, env: dict) -> dict:
        """Derive the `reflex export` env from the runtime env.

        The build env makes the compiled bundle instance-independent:
        - the api_url is `http://localhost:<external app port>`: the reflex client
          rewrites a literal `localhost` hostname to `window.location.hostname` at
          runtime (and drops the port under https), so the bundle carries no
          instance host. Under local http the external port matches because every
          app host is served on that single shared nginx port.
        - REFLEX_BACKEND_PATH prefixes the baked endpoint URLs; the front nginx
          block proxies that prefix (unstripped) to the instance's backend, which
          runs with the same REFLEX_BACKEND_PATH so paths and the socket.io
          namespace match.
        - GWS_REFLEX_BUILD_MODE tells gws_reflex state code to bake neutral values
          (no app id, no auth info) into the initial state.
        """
        build_env = dict(env)
        build_env["GWS_REFLEX_API_URL"] = f"http://localhost:{Settings.get_app_external_port()}"
        build_env["REFLEX_BACKEND_PATH"] = ReflexProcess.BACKEND_PATH
        build_env[ReflexProcess.BUILD_MODE_ENV_VAR] = "1"
        return build_env

    def _get_prod_nginx_services(self, front_build_folder: str) -> list[AppNginxServiceInfo]:
        services: list[AppNginxServiceInfo] = []

        # In prod mode, we serve the front from the build folder
        services.append(
            AppNginxReflexFrontServerServiceInfo(
                service_id=self.get_id() + "-front",
                source_port=self.get_service_source_port(),
                server_name=self.get_front_server_names(),
                front_folder_path=front_build_folder,
                # same-origin backend routing for builds baked with BACKEND_PATH
                backend_port=self.back_port,
                backend_path=ReflexProcess.BACKEND_PATH,
            )
        )

        # the back is always served by a redirect service
        services.append(self._get_cloud_back_nginx_services())

        return services

    def _get_cloud_back_nginx_services(self) -> AppNginxServiceInfo:
        return AppNginxRedirectServiceInfo(
            service_id=self.get_id() + "-back",
            source_port=self.get_service_source_port(),
            # the backend host stays id-based only (the custom subdomain is a front-only alias)
            server_name=self.get_host_name("-back"),
            destination_port=self.back_port,
            # the back is always served by a redirect service.
            # Allow CORS from the front origin(s): the id-based host and, when set, the
            # custom-subdomain alias from which the front may also be served.
            allowed_origins=self._get_front_origins(),
        )

    def _get_front_origins(self) -> list[str]:
        """Front origins allowed to call the backend: the id-based host plus the custom alias."""
        origins = [self.get_host_url()]
        custom_url = self.get_custom_host_url()
        if custom_url is not None:
            origins.append(custom_url)
        return origins

    def _refresh_custom_subdomain_services(self) -> None:
        """Refresh the front server_name alias and the backend CORS allow-list in place.

        The front static server gains/loses the custom host alias; the backend keeps its
        id-based host but must allow the custom front origin so the (still id-based) backend
        accepts cross-origin calls from a front served on the custom domain.
        """
        for service in self._services:
            if isinstance(service, AppNginxReflexFrontServerServiceInfo):
                service.server_name = self.get_front_server_names()
            elif service.service_id.endswith("-back") and isinstance(
                service, AppNginxRedirectServiceInfo
            ):
                service.allowed_origins = list(dict.fromkeys(self._get_front_origins()))

    def get_back_host_url(self) -> str:
        return self.get_host_url("-back")

    def call_health_check(self) -> bool:
        # health check for both front and back
        try:
            # in prod the backend endpoints are mounted under BACKEND_PATH; dev serves at root
            ping_prefix = "" if self._app.is_dev_mode() else ReflexProcess.BACKEND_PATH
            ExternalApiService.get(
                f"http://localhost:{self.back_port}{ping_prefix}/ping",
                raise_exception_if_error=True,
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
        return port in (self.front_port, self.back_port)

    def get_ports(self) -> list[int]:
        return [self.front_port, self.back_port]

    def build_handoff_url(self, host_url: str, code: str) -> str:
        """Keep the query-param handoff — the reflex front is a static host + separate backend, so
        the cookie-session flow doesn't map cleanly yet. The app exchanges gws_code for a JWT
        itself (no reload survival for now).
        """
        return f"{host_url}?{app_gateway_constants.GWS_CODE_QUERY_PARAM}={code}"

    def _get_log_level_option(self) -> str:
        return f"--loglevel={Logger.get_instance().level.lower()}"

    @classmethod
    def _get_cached_reflex_access_token(cls) -> str:
        """Get cached reflex access token if valid, otherwise retrieve and cache new one"""
        Logger.debug("Retrieving reflex access token")
        reflex_access_token = Settings.get_reflex_access_token()
        if reflex_access_token:
            Logger.debug("Using reflex access token from Settings")
            return reflex_access_token

        with cls._token_cache_lock:
            current_time = time.time()

            # Check if cache is still valid
            if (
                cls._cached_access_token is not None
                and cls._cache_timestamp is not None
                and current_time - cls._cache_timestamp < cls._cache_duration_seconds
            ):
                cache_age = current_time - cls._cache_timestamp
                Logger.debug(
                    f"Using cached reflex access token (age: {cache_age:.0f}s, "
                    f"ttl: {cls._cache_duration_seconds}s)"
                )
                return cls._cached_access_token

            # Cache is invalid, retrieve new token
            Logger.debug(
                "Reflex access token cache invalid or missing, fetching new token from SpaceService"
            )
            space_service = SpaceService.get_instance()
            new_token = space_service.get_reflex_access_token()
            Logger.debug(
                f"Fetched new reflex access token (length: {len(new_token) if new_token else 0})"
            )

            # Update cache
            cls._cached_access_token = new_token
            cls._cache_timestamp = current_time

            return new_token
