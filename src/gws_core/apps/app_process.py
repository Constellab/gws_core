import os
import time
from abc import abstractmethod
from datetime import datetime
from threading import Thread

import psutil

from gws_core.apps.app_dto import (
    AppInstanceConfigDTO,
    AppInstanceUrl,
    AppProcessStatus,
    AppProcessStatusDTO,
)
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.app_nginx_service import AppNginxServiceInfo
from gws_core.core.exception.exceptions.unauthorized_exception import UnauthorizedException
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.execution_context import ExecutionContext
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class AppProcessStartResult:
    process: SysProc
    services: list[AppNginxServiceInfo]

    def __init__(self, process: SysProc, services: list[AppNginxServiceInfo]):
        self.process = process
        self.services = services


class AppProcess:
    """Process of an app. A process is an instance of a running command that serves a single app.

    The app is served on local ports. A Nginx reverse proxy is used to
    expose the app on the host URL.
    """

    _token: str

    _app: AppInstance

    _process: SysProc | None
    _working_dir: str | None

    # number of successive check when there is not connection to the main app
    _current_no_connection_check: int

    _check_is_running: bool

    _services: list[AppNginxServiceInfo]
    # Status tracking
    _status: AppProcessStatus
    _status_text: str

    _started_at: datetime | None
    _started_by: User | None

    # interval in second to check if the app is still used
    CHECK_RUNNING_INTERVAL = 30

    # timeout in second to wait for the main app to start
    START_APP_TIMEOUT = 30

    # number of successive check when there is not connection to the main app
    # before killing it
    SUCCESSIVE_CHECK_BEFORE_KILL = 3

    DEV_MODE_APP_ID = "dev-app"
    APP_CONFIG_FILENAME = "app_config.json"
    DEV_MODE_USER_ACCESS_TOKEN_KEY = "dev_mode_token"

    def __init__(self, app: AppInstance):
        """Initialize the app process.

        Note: The app is not generated here. Generation happens on first start.

        :param app: The app instance to manage
        """
        self._token = StringHelper.generate_random_chars(50)
        self._services = []
        self._status = AppProcessStatus.STOPPED
        self._status_text = ""
        self._process = None
        self._working_dir = None
        self._app = app

        self._check_is_running = False
        self._current_no_connection_check = 0
        # User access tokens: maps user_access_token -> user_id
        self._user_access_tokens: dict[str, str] = {}
        self._started_at = None
        self._started_by = None

    @abstractmethod
    def _start_process(self, app: AppInstance) -> AppProcessStartResult:
        """Start the process for the app"""

    @abstractmethod
    def call_health_check(self) -> bool:
        """Call the health check of the app to check if it is still running"""

    @abstractmethod
    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""

    def get_status(self) -> AppProcessStatus:
        """Get the current status of the app process"""
        return self._status

    def is_stopped(self) -> bool:
        """Check if the app process is stopped"""
        return self._status == AppProcessStatus.STOPPED

    def is_running(self) -> bool:
        """Check if the app process is running"""
        return self._status == AppProcessStatus.RUNNING

    def is_starting(self) -> bool:
        """Check if the app process is starting"""
        return self._status == AppProcessStatus.STARTING

    def get_status_text(self) -> str:
        """Get the current status text of the app process"""
        return self._status_text

    def set_status(self, status: AppProcessStatus, status_text: str = ""):
        """Set the status and status text of the app process"""
        self._status = status
        self._status_text = status_text
        Logger.debug(
            f"App process {self._app.resource_model_id} status changed to {status.value}: {status_text}"
        )

    def get_token(self) -> str:
        """Get the token of the app process.
        This is used to secure the app and allow access to it.
        """
        return self._token

    def start_app_async(self) -> None:
        """Start the process for the app.

        The app will be generated on first start if not already done.
        """

        if self._status != AppProcessStatus.STOPPED:
            return

        if self._app is None:
            raise Exception("No app set for this process")

        self.set_status(AppProcessStatus.STARTING, "Starting app...")

        try:
            self._save_config()

            thread = Thread(target=self._start_app_and_watch, args=(self._app,))
            thread.start()
        except Exception as e:
            Logger.error("Error while starting app, killing the process")
            self.stop_process()
            raise e

    def _start_app_and_watch(self, app: AppInstance) -> None:
        try:
            self._started_at = datetime.now()
            self._started_by = CurrentUserService.get_current_user() or User.get_and_check_sysuser()
            result = self._start_process(app)
            self._process = result.process
            self._services = result.services

            if self._services:
                AppNginxManager.get_instance().register_services(self._services)

            self._current_no_connection_check = 0

            self.set_status(AppProcessStatus.STARTING, "Waiting for app to be ready...")
            self.wait_main_app_health_check()

            self.set_status(AppProcessStatus.RUNNING, "App running successfully")

            self.start_check_running()
        except Exception as e:
            Logger.error(f"Error while starting app {app.resource_model_id}: {e}")
            self.stop_process()
            raise e

    def wait_main_app_health_check(self) -> None:
        # wait until ping http://localhost:8080/healthz  returns 200
        i = 0
        while True:
            time.sleep(1)

            health_check = self.call_health_check()
            if health_check:
                break
            Logger.debug("Waiting for app to start")
            i += 1
            if i > self.START_APP_TIMEOUT:
                self.set_status(
                    AppProcessStatus.STOPPED,
                    "The app did not start in time, please check the logs for more details or retry later.",
                )
                raise Exception(
                    "The app did not start in time, please check the logs for more details or retry later."
                )

    def get_working_dir(self) -> str:
        """Get the working directory for this app process.

        The directory is created when the app is first started.
        Raises an exception if called before the app is generated.

        :return: The working directory path
        :raises Exception: If the working directory has not been created yet
        """
        if self._working_dir is None:
            self._working_dir = Settings.make_temp_dir()
        return self._working_dir

    def stop_process(self) -> None:
        """Kill the process and the app"""
        if self.is_stopped():
            return

        Logger.debug("Killing the app")
        if self._process is not None:
            self._process.kill_with_children()
            self._process = None

        self._current_no_connection_check = 0

        # Delete working directory if it was created
        if self._working_dir is not None:
            FileHelper.delete_dir(self._working_dir)

        if self._services:
            # unregister the nginx services
            services_ids = [service.service_id for service in self._services]
            AppNginxManager.get_instance().unregister_services(services_ids)
        self._services = []

        self.set_status(AppProcessStatus.STOPPED, "Process stopped")

    def get_host_name(self, suffix: str = "") -> str:
        """Get the host name for the app process based on the port and suffix.
        This is used to generate the host URL for the app.
        We use the resource_model_id as host name to have a stable URL for the app.
        The stable URL is required for reflex as the backend url is stored in the front build and should not change at each deployment.
        """
        host_name = self.DEV_MODE_APP_ID if self._app.is_dev_mode() else self._app.resource_model_id

        if Settings.is_local_or_desktop_env():
            return f"{host_name}{suffix}.localhost"

        sub_domain = Settings.get_app_sub_domain()
        virtual_host = Settings.get_virtual_host()

        return f"{sub_domain}-{host_name}{suffix}.{virtual_host}"

    def get_host_url(self, suffix: str = "") -> str:
        if Settings.is_local_or_desktop_env():
            # In local we use a subdomain with localhost and the external port
            # like http://appid.localhost:8501. This allows to have multiple apps
            return f"http://{self.get_host_name(suffix)}:{Settings.get_app_external_port()}"
        else:
            return f"https://{self.get_host_name(suffix)}"

    def get_app_full_url(self) -> AppInstanceUrl:
        """Get the full URL for the app with authentication tokens.

        This method handles user authentication and generates access tokens.

        :param app_id: The app ID
        :return: The app URL with parameters
        """
        host_url = self.get_host_url()

        if self._app.is_dev_mode():
            # Dev mode handling
            if self._app._dev_user_id:
                # add the dev user to the list of users that can access the app
                self._add_user(self._app._dev_user_id, self.DEV_MODE_USER_ACCESS_TOKEN_KEY)
            else:
                # add the system user to the list of users that can access the app
                # in dev mode, we authenticate the system user
                self._add_user(User.get_and_check_sysuser().id, self.DEV_MODE_USER_ACCESS_TOKEN_KEY)
            return AppInstanceUrl(host_url=host_url)

        # Normal mode handling
        params = {"gws_token": self._token, "gws_app_id": self._app.resource_model_id}

        user: User | None = None
        if self._app.requires_authentication:
            user = CurrentUserService.get_current_user()
        else:
            user = User.get_and_check_sysuser()

        if not user:
            raise UnauthorizedException(
                f"The user could not be be authenticated with requires_authentication : {self._app.requires_authentication}"
            )

        user_access_token = self._add_user(user.id)
        params["gws_user_access_token"] = user_access_token

        return AppInstanceUrl(host_url=host_url, params=params)

    def get_service_source_port(self) -> int:
        return Settings.get_app_external_port()

    def _get_common_env_variables(self, execution_context: ExecutionContext) -> dict[str, str]:
        """Get common environment variables for the app process."""
        env_vars = {
            "GWS_APP_ID": self._app.resource_model_id,
            "GWS_APP_TOKEN": self.get_token(),
            "GWS_IS_VIRTUAL_ENV": str(self._app.is_virtual_env_app()),
            "GWS_APP_CONFIG_FILE_PATH": self._get_app_config_path(),
            "GWS_IS_TEST_ENV": str(Settings.get_instance().is_test),
            "GWS_IS_DEV_MODE": str(self._app.is_dev_mode()),
            "GWS_REQUIRES_AUTHENTICATION": str(self._app.requires_authentication),
            ExecutionContext.get_os_env_name(): execution_context.value,
        }
        return env_vars

    ############################################ APP CONFIG ############################################

    def _save_config(self) -> None:
        """Save the config file to the app directory.
        If the config file already exists, it is updated.
        Otherwise, a new config file is created.

        :param config: The configuration DTO to write
        """
        config_path = self._get_app_config_path()

        config: AppInstanceConfigDTO
        if os.path.exists(config_path):
            config = self._read_config_file()
            # update the config with current user access tokens
            config.user_access_tokens = self._user_access_tokens
        else:
            str_resources: list[str] = []

            app_resources = self._app.resources or []
            if self._app.is_virtual_env_app():
                # for virtual env app, the resources are the file paths
                str_resources = [
                    resource.path for resource in app_resources if isinstance(resource, FSNode)
                ]
            else:
                # for normal app, the resources are the model ids
                str_resources: list[str] = []

                # if the str_resources contains None, raise an exception
                for res in app_resources:
                    model_id = res.get_model_id()
                    if model_id is None:
                        raise Exception(
                            f"Resource in app {self._app.resource_model_id} does not have a model ID"
                        )
                    str_resources.append(model_id)

            config = AppInstanceConfigDTO(
                source_ids=str_resources,
                params=self._app.params,
                user_access_tokens=self._user_access_tokens,
            )

        with open(config_path, "w", encoding="utf-8") as file_path:
            file_path.write(config.to_json_str())

    def _read_config_file(self) -> AppInstanceConfigDTO:
        """Read the config file from the app directory.

        :return: The configuration DTO
        """
        config_path = self._get_app_config_path()
        with open(config_path, encoding="utf-8") as file_path:
            content = file_path.read()
            return AppInstanceConfigDTO.from_json_str(content)

    def _get_app_config_path(self) -> str:
        """Get the path to the app config file."""
        return os.path.join(self.get_working_dir(), self.APP_CONFIG_FILENAME)

    ############################################ USER ############################################

    def _add_user(self, user_id: str, user_access_token: str | None = None) -> str:
        """Add the user to the list of users that can access the app and return the user access token.

        User tokens are stored in memory only.

        :param user_id: The user ID to add
        :param user_access_token: Optional pre-generated token to use
        :return: The user access token
        """
        # check if the user is already in the list
        for token, user_access_id in self._user_access_tokens.items():
            if user_id == user_access_id:
                return token

        if not user_access_token:
            user_access_token = (
                StringHelper.generate_uuid() + "_" + str(DateHelper.now_utc_as_milliseconds())
            )

        # Store in memory
        self._user_access_tokens[user_access_token] = user_id

        # Store in config file
        self._save_config()

        return user_access_token

    def get_user_id_from_token(self, user_access_token: str) -> str | None:
        """Get the user id from the user access token.
        If the user does not exist, return None.

        :param user_access_token: The user access token
        :return: The user ID or None
        """
        return self._user_access_tokens.get(user_access_token, None)

    def user_has_access_to_app(self, user_access_token: str) -> str | None:
        """Return the user id from the user access token if the user has access to the app.

        :param user_access_token: The user access token
        :return: The user ID or None if not found
        """

        return self.get_user_id_from_token(user_access_token)

    ############################################ CHECK RUNNING ############################################

    def start_check_running(self) -> None:
        """
        Method to start the check running loop to check if the app is still used
        """
        # do not start multiple check running loops
        if self._check_is_running:
            return

        self._check_is_running = True
        self._check_running_loop()

    def _check_running_loop(self) -> None:
        try:
            while True:
                time.sleep(self.CHECK_RUNNING_INTERVAL)
                Logger.debug("Checking running app")

                # stop the loop if the status was changed to stopped
                if not self.is_running():
                    Logger.debug("App process is not running, stopping the check running loop")
                    self.stop_process()
                    return

                if not self.subprocess_is_running():
                    Logger.debug("Subprocess is not running, stopping the app")
                    self.stop_process()
                    return
                # if there is not more connection to the app, we stop it
                # In dev mode, we do not stop the app even if there is no connection
                if not self._app.is_dev_mode() and not self._check_running():
                    Logger.debug("No more connection to the app, stopping the app")
                    self.stop_process()
                    return

        finally:
            self._check_is_running = False

    def subprocess_is_running(self) -> bool:
        return self._process is not None and self._process.is_alive()

    def _check_running(self) -> bool:
        try:
            # count the number of network connections of the app
            connection_count = self.count_connections()

            Logger.debug(f"App has {connection_count} connections")
            if connection_count <= 0:
                # if connection_count <= 0 or connection_count < app.default_number_of_connection:
                self._current_no_connection_check += 1

                if self._current_no_connection_check >= self.SUCCESSIVE_CHECK_BEFORE_KILL:
                    Logger.debug("No connections, killing the app")
                    return False

            else:
                self._current_no_connection_check = 0

            return True
        except Exception as e:
            # if an error occurs, we assume the app is still running
            Logger.error(f"Error while checking running app: {e}")
            return True

    def count_connections(self) -> int:
        if not self._process:
            return 0

        # get the list of the connections
        connections = psutil.net_connections(kind="inet")

        pid_with_children = [child.pid for child in self._process.get_all_children()]
        pid_with_children.append(self._process.pid)

        return len(
            [x for x in connections if x.pid in pid_with_children and x.status == "ESTABLISHED"]
        )

    def get_id(self) -> str:
        return self._app.resource_model_id

    def get_status_dto(self) -> AppProcessStatusDTO:
        return AppProcessStatusDTO(
            id=self.get_id(),
            status=self._status,
            status_text=self._status_text,
            app=self._app.to_dto(),
            nb_of_connections=self.count_connections(),
            config_file_path=self._get_app_config_path(),
            started_at=self._started_at,
            started_by=self._started_by.to_dto() if self._started_by else None,
        )

    ############################################ UTILS ############################################

    def get_current_user_theme(self) -> FrontTheme:
        user = CurrentUserService.get_current_user()

        if user and user.has_dark_theme():
            return FrontService.get_dark_theme()

        return FrontService.get_light_theme()

    def _get_and_check_shell_proxy(self, app_instance: AppInstance) -> ShellProxy:
        # check if the env is installed
        # if should be installed by the task that generated the app
        # otherwise the env would installed when the user open the app, leading to a long loading time
        shell_proxy = app_instance.get_shell_proxy()
        if isinstance(shell_proxy, BaseEnvShell) and not shell_proxy.env_is_installed():
            self.set_status(
                AppProcessStatus.STARTING, "Installing virtual environment (it may take a while)..."
            )
            shell_proxy.install_env()
        return shell_proxy

    def wait_for_start(self) -> AppProcessStatus:
        """Wait for the process to start"""
        i = 0
        while self.is_starting() and i < self.START_APP_TIMEOUT:
            time.sleep(1)  # wait for 1 second
            i += 1

        return self.get_status()
