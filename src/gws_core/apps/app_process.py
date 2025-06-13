

import time
from abc import abstractmethod
from threading import Thread
from typing import Dict

import psutil

from gws_core.apps.app_dto import AppInstanceUrl, AppProcessStatusDTO
from gws_core.apps.app_instance import AppInstance
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.user.current_user_service import CurrentUserService


class AppProcess:

    host_url: str = None

    _token: str = None

    env_hash: str = None

    current_running_apps: Dict[str, AppInstance] = None

    _process: SysProc = None
    _working_dir: str = None

    # number of successive check when there is not connection to the main app
    _current_no_connection_check: int = 0

    _check_is_running: bool = False

    # interval in second to check if the app is still used
    CHECK_RUNNING_INTERVAL = 30

    # timeout in second to wait for the main app to start
    START_APP_TIMEOUT = 30

    # number of successive check when there is not connection to the main app
    # before killing it
    SUCCESSIVE_CHECK_BEFORE_KILL = 3

    def __init__(self, host_url: str, env_hash: str = None):
        self.host_url = host_url
        self.env_hash = env_hash
        self._token = StringHelper.generate_random_chars(50)
        self.current_running_apps = {}

    @abstractmethod
    def _start_process(self, app: AppInstance) -> SysProc:
        """Start the process for the app"""

    @abstractmethod
    def call_health_check(self) -> bool:
        """Call the health check of the app to check if it is still running"""

    @abstractmethod
    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""

    def add_app_and_start_process(self, app: AppInstance) -> None:
        """Start the process for the app"""
        app.generate_app(self.get_working_dir())

        self._process = self._start_process(app)

        self._current_no_connection_check = 0

        try:
            self.wait_main_app_health_check()
        except Exception as e:
            Logger.error("Error while starting streamlit app, killing the process")
            self.stop_process()
            raise e

        self.start_check_running()

        self.current_running_apps[app.app_id] = app

    def add_app_to_process(self, app: AppInstance) -> None:
        """Add the app to an existing process.

        :param app: _description_
        :type app: AppInstance
        """
        app.generate_app(self.get_working_dir())
        self.current_running_apps[app.app_id] = app

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
                raise Exception("The app did not start in time, please check the logs for more details or retry later.")

    def process_is_running(self) -> bool:
        return self._process is not None and self._process.is_alive()

    def get_working_dir(self) -> str:
        if self._working_dir is None:
            self._working_dir = Settings.make_temp_dir()
        return self._working_dir

    def stop_process(self) -> None:
        """Kill the process and all apps
        """
        if self._process is not None:
            self._process.kill_with_children()
            self._process = None

        for app in self.current_running_apps.values():
            app.destroy()

        self.current_running_apps = {}
        self._current_no_connection_check = 0

    def has_app(self, app_id: str) -> bool:
        return app_id in self.current_running_apps

    def get_app(self, app_id: str) -> AppInstance | None:
        return self.current_running_apps.get(app_id)

    def user_has_access_to_app(self, app_id: str, user_access_token: str) -> str | None:
        """Return the user id from the user access token if the user has access to the app
        """
        app = self.get_app(app_id)
        if not app:
            return None

        return app.get_user_from_token(user_access_token)

    def find_app_by_resource_model_id(self, resource_model_id: str) -> AppInstance | None:
        """Find the app that was generated from the given resource model id
        """
        for app in self.current_running_apps.values():
            if app.was_generated_from_resource_model_id(resource_model_id):
                return app

        return None

    def get_app_full_url(self, app_id: str) -> AppInstanceUrl:
        app = self.get_app(app_id)
        if not app:
            raise Exception(f"App {app_id} not found")

        return app.get_app_full_url(self.host_url, self._token)

    ############################################ CHECK RUNNING ############################################

    def start_check_running(self) -> None:
        """
        Method to start the check running loop to check if the app is still used
        """
        if self._check_is_running:
            return

        self._check_is_running = True
        Thread(target=self._check_running_loop).start()

    def _check_running_loop(self) -> None:
        while self.process_is_running():
            time.sleep(self.CHECK_RUNNING_INTERVAL)
            Logger.debug("Checking running app")

            try:
                if not self._check_running():
                    break
            except Exception as e:
                Logger.error(f"Error while checking running app: {e}")

        Logger.debug("Killing the app")
        self.stop_process()

        self._check_is_running = False

    def _check_running(self) -> bool:
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

    def count_connections(self) -> int:
        if not self._process:
            return 0

        # get the list of the connections
        connections = psutil.net_connections(kind='inet')

        pid_with_children = [child.pid for child in self._process.get_all_children()]
        pid_with_children.append(self._process.pid)

        return len([x for x in connections if x.pid in pid_with_children and x.status == 'ESTABLISHED'])

    def get_status_dto(self) -> AppProcessStatusDTO:
        return AppProcessStatusDTO(
            id=self.env_hash,
            status="RUNNING" if self.process_is_running() else "STOPPED",
            running_apps=[app.to_dto() for app in self.current_running_apps.values()],
            nb_of_connections=self.count_connections(),
        )

    ############################################ UTILS ############################################

    def get_current_user_theme(self) -> FrontTheme:
        user = CurrentUserService.get_current_user()

        if user and user.has_dark_theme():
            return FrontService.get_dark_theme()

        return FrontService.get_light_theme()
