

import os
import time
from threading import Thread
from typing import Dict, Optional

import psutil

from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.streamlit.streamlit_app import StreamlitApp, StreamlitAppUrl
from gws_core.streamlit.streamlit_dto import StreamlitProcessStatusDTO
from gws_core.streamlit.streamlit_plugin import StreamlitPlugin
from gws_core.user.current_user_service import CurrentUserService


class StreamlitProcess:
    """Object representing a streamlit process, one instance of 'streamlit run' command.
    It can manage multiple streamlit apps using the same environment.
    """

    port: int = None
    host_url: str = None

    _token: str = None

    env_hash: str = None

    current_running_apps: Dict[str, StreamlitApp] = None

    _process: SysProc = None
    _working_dir: str = None

    # number of successive check when there is not connection to the main app
    _current_no_connection_check: int = 0

    _check_is_running: bool = False

    _dev_mode: bool = False
    _dev_config_file: str = None

    # interval in second to check if the app is still used
    CHECK_RUNNING_INTERVAL = 30

    # number of successive check when there is not connection to the main app
    # before killing it
    SUCCESSIVE_CHECK_BEFORE_KILL = 3

    def __init__(self, port: int, host_url: str, env_hash: str = None):
        self.port = port
        self.host_url = host_url
        self.env_hash = env_hash
        self._token = StringHelper.generate_random_chars(50)
        self.current_running_apps = {}

    def create_app(self, app: StreamlitApp) -> None:
        app.generate_app(self.get_working_dir())
        self.current_running_apps[app.app_id] = app

    def set_dev_mode(self, dev_config_file: str) -> None:
        self._dev_mode = True
        self._dev_config_file = dev_config_file

    def start_streamlit_process(self, app: StreamlitApp) -> None:
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

        # check if the env is installed
        # if should be installed by the task that generated the app
        # otherwise the env would installed when the user open the app, leading to a long loading time
        shell_proxy = app.get_shell_proxy()
        if isinstance(shell_proxy, BaseEnvShell) and not shell_proxy.env_is_installed():
            raise Exception(
                "The virtual environment is not installed, it was deleted. Please re-execute the task that generated the app to re-install the virtual environment.")

        # Must use the shell_mode=False to retrieve the correct pid to check the number of connections
        self._process = shell_proxy.run_in_new_thread(cmd, shell_mode=False)

        self._current_no_connection_check = 0

        try:
            self.wait_main_app_heath_check()
        except Exception as e:
            Logger.error("Error while starting streamlit app, killing the process")
            self.stop_process()
            raise e

        self.start_check_running()

    def wait_main_app_heath_check(self) -> None:
        # wait until ping http://localhost:8080/healthz  returns 200
        i = 0
        while True:
            time.sleep(1)

            health_check = self.call_health_check()
            if health_check:
                break
            Logger.debug("Waiting for streamlit app to start")
            i += 1
            if i > 30:
                raise Exception("Streamlit app did not start in time")

    def call_health_check(self) -> bool:
        try:
            ExternalApiService.get(f"http://localhost:{self.port}/healthz")
        except Exception:
            return False

        return True

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
            self._process.kill()
            self._process = None

        for app in self.current_running_apps.values():
            app.destroy()

        self.current_running_apps = {}
        self._current_no_connection_check = 0

    def has_app(self, app_id: str) -> bool:
        return app_id in self.current_running_apps

    def get_app(self, app_id: str) -> StreamlitApp | None:
        return self.current_running_apps.get(app_id)

    def get_app_full_url(self, app_id: str) -> StreamlitAppUrl:
        app = self.get_app(app_id)
        if not app:
            raise Exception(f"App {app_id} not found")

        return app.get_app_full_url(self.host_url, self._token)

    def get_status_dto(self) -> StreamlitProcessStatusDTO:
        return StreamlitProcessStatusDTO(
            id=self.env_hash,
            status="RUNNING" if self.process_is_running() else "STOPPED",
            running_apps=[app.to_dto(self.host_url, self._token) for app in self.current_running_apps.values()],
            nb_of_connections=self.count_connections(),
        )

    def user_has_access_to_app(self, app_id: str, user_access_token: str) -> Optional[str]:
        """Return the user id from the user access token if the user has access to the app
        """
        app = self.get_app(app_id)
        if not app:
            return None

        return app.get_user_from_token(user_access_token)

    def find_app_by_resource_model_id(self, resource_model_id: str) -> StreamlitApp:
        """Find the streamlit app that was generated from the given resource model id
        """
        for app in self.current_running_apps.values():
            if app.was_generated_from_resource_model_id(resource_model_id):
                return app

        return None

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
            Logger.debug("Checking running streamlit app")

            try:
                if not self._check_running():
                    break
            except Exception as e:
                Logger.error(f"Error while checking running streamlit app: {e}")

        Logger.debug("Killing the streamlit app")
        self.stop_process()

        self._check_is_running = False

    def _check_running(self) -> bool:
        # count the number of network connections of the app
        connection_count = self.count_connections()

        Logger.debug(f"Streamlit main app has {connection_count} connections")
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

        return len([x for x in connections if x.pid == self._process.pid and x.status == 'ESTABLISHED'])

    ############################################ UTILS ############################################

    def get_current_user_theme(self) -> FrontTheme:
        user = CurrentUserService.get_current_user()

        if user and user.has_dark_theme():
            return FrontService.get_dark_theme()

        return FrontService.get_light_theme()
