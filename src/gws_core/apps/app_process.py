import time
from abc import abstractmethod
from threading import Thread

import psutil

from gws_core.apps.app_dto import AppInstanceUrl, AppProcessStatus, AppProcessStatusDTO
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.app_nginx_service import AppNginxServiceInfo
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.user.current_user_service import CurrentUserService


class AppProcessStartResult:
    process: SysProc
    services: list[AppNginxServiceInfo]

    def __init__(self, process: SysProc, services: list[AppNginxServiceInfo]):
        self.process = process
        self.services = services


class AppProcess:
    """Process of an app. A process is an instance of a running command that serves the app.

    A process can have multiple apps running in it.

    The apps are served on local ports. A Nginx reverse proxy is used to
    expose the apps on the host URL.All the apps are externally exposed to the
    same port, but depending on the sub domain, the local reverse proxy will
    redirect the request to the correct app.
    """

    id: str = None

    _token: str = None

    env_hash: str = None

    current_running_apps: dict[str, AppInstance] = None

    is_dev_mode: bool = None

    _process: SysProc = None
    _working_dir: str = None

    # number of successive check when there is not connection to the main app
    _current_no_connection_check: int = 0

    _check_is_running: bool = False

    _services: list[AppNginxServiceInfo] = None

    # Status tracking
    _status: AppProcessStatus = AppProcessStatus.STOPPED
    _status_text: str = ""

    # interval in second to check if the app is still used
    CHECK_RUNNING_INTERVAL = 30

    # timeout in second to wait for the main app to start
    START_APP_TIMEOUT = 30

    # number of successive check when there is not connection to the main app
    # before killing it
    SUCCESSIVE_CHECK_BEFORE_KILL = 3

    def __init__(self, id_: str, env_hash: str = None):
        self.id = id_
        self.env_hash = env_hash
        self._token = StringHelper.generate_random_chars(50)
        self.current_running_apps = {}
        self._services = []
        self._status = AppProcessStatus.STOPPED
        self._status_text = ""

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
        Logger.debug(f"App process {self.id} status changed to {status.value}: {status_text}")

    def get_token(self) -> str:
        """Get the token of the app process.
        This is used to secure the app and allow access to it.
        """
        return self._token

    def add_app_if_not_exists(self, app: AppInstance) -> None:
        """Add an app to the process."""
        if self.is_dev_mode is None:
            self.is_dev_mode = app.is_dev_mode()

        if app.is_dev_mode() != self.is_dev_mode:
            raise Exception("Cannot add an app with a different dev mode to the process")

        if app.resource_model_id in self.current_running_apps:
            return

        try:
            app.generate_app(self.get_working_dir())
        except Exception as e:
            Logger.error(f"Error while generating app {app.resource_model_id}: {e}")
            raise e

        self.current_running_apps[app.resource_model_id] = app

    def start_app_async(self, app_id: str) -> None:
        """Start the process for the app using app_id"""

        if self._status != AppProcessStatus.STOPPED:
            return
        # Find the app instance
        app = self.get_app(app_id)

        self.set_status(AppProcessStatus.STARTING, "Starting app...")

        try:
            thread = Thread(target=self._start_app_and_watch, args=(app,))
            thread.start()
        except Exception as e:
            Logger.error("Error while starting streamlit app, killing the process")
            self.stop_process()
            raise e

    def _start_app_and_watch(self, app: AppInstance) -> None:
        try:
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
                raise Exception("The app did not start in time, please check the logs for more details or retry later.")

    def get_working_dir(self) -> str:
        if self._working_dir is None:
            self._working_dir = Settings.make_temp_dir()
        return self._working_dir

    def stop_process(self) -> None:
        """Kill the process and all apps"""
        if self.is_stopped():
            return

        Logger.debug("Killing the app")
        if self._process is not None:
            self._process.kill_with_children()
            self._process = None

        for app in self.current_running_apps.values():
            app.destroy()
        self.current_running_apps = {}

        self.current_running_apps = {}
        self._current_no_connection_check = 0

        FileHelper.delete_dir(self.get_working_dir())

        if self._services:
            # unregister the nginx services
            services_ids = [service.service_id for service in self._services]
            AppNginxManager.get_instance().unregister_services(services_ids)
        self._services = []

        self.set_status(AppProcessStatus.STOPPED, "Process stopped")

    def has_app(self, app_id: str) -> bool:
        return app_id in self.current_running_apps

    def get_app(self, app_id: str) -> AppInstance | None:
        return self.current_running_apps.get(app_id)

    def get_and_check_app(self, app_id: str) -> AppInstance:
        """Get the app instance and check if it exists"""
        app = self.get_app(app_id)
        if not app:
            raise Exception(f"App with ID {app_id} not found in process")
        return app

    def user_has_access_to_app(self, app_id: str, user_access_token: str) -> str | None:
        """Return the user id from the user access token if the user has access to the app"""
        app = self.get_app(app_id)
        if not app:
            return None

        return app.get_user_from_token(user_access_token)

    def find_app_by_resource_model_id(self, resource_model_id: str) -> AppInstance | None:
        """Find the app that was generated from the given resource model id"""
        for app in self.current_running_apps.values():
            if app.was_generated_from_resource_model_id(resource_model_id):
                return app

        return None

    def get_host_name(self, suffix: str = "") -> str:
        """Get the host name for the app process based on the port and suffix.
        This is used to generate the host URL for the app.
        """

        if Settings.is_local_or_desktop_env():
            return f"{self.id}{suffix}.localhost"

        sub_domain = Settings.get_app_sub_domain()
        virtual_host = Settings.get_virtual_host()

        return f"{sub_domain}-{self.id}{suffix}.{virtual_host}"

    def get_host_url(self) -> str:
        if Settings.is_local_or_desktop_env():
            return f"http://{self.get_host_name()}:{Settings.get_app_external_port()}"
        else:
            return f"https://{self.get_host_name()}"

    def get_app_full_url(self, app_id: str) -> AppInstanceUrl:
        app = self.get_and_check_app(app_id)
        return app.get_app_full_url(self.get_host_url(), self._token)

    def get_service_source_port(self) -> int:
        return Settings.get_app_external_port()

    ############################################ CHECK RUNNING ############################################

    def start_check_running(self) -> None:
        """
        Method to start the check running loop to check if the app is still used
        """
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
                if not self._check_running():
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

        return len([x for x in connections if x.pid in pid_with_children and x.status == "ESTABLISHED"])

    def get_status_dto(self) -> AppProcessStatusDTO:
        return AppProcessStatusDTO(
            id=self.env_hash,
            status=self._status,
            status_text=self._status_text,
            running_apps=[app.to_dto() for app in self.current_running_apps.values()],
            nb_of_connections=self.count_connections(),
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
            self.set_status(AppProcessStatus.STARTING, "Installing virtual environment (it may take a while)...")
            shell_proxy.install_env()
        return shell_proxy

    def wait_for_start(self) -> AppProcessStatus:
        """Wait for the process to start"""
        i = 0
        while self.is_starting() and i < self.START_APP_TIMEOUT:
            time.sleep(1)  # wait for 1 second
            i += 1

        return self.get_status()
