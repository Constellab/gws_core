

import os
import time
from threading import Thread
from typing import Dict, List

import psutil

from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_dto import StreamlitStatusDTO
from gws_core.user.current_user_service import CurrentUserService


class StreamlitAppManager():
    """Class to manage the different streamlit apps

    Each apps runs on the same streamlit server managed by the _main_streamlit_app
    """

    # interval in second to check if the app is still used
    CHECK_RUNNING_INTERVAL = 30

    # number of successive check when there is not connection to the main app
    # before killing it
    SUCCESSIVE_CHECK_BEFORE_KILL = 3

    MAIN_APP_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "_main_streamlit_app.py")

    main_app_token: str = None
    main_app_process: SysProc = None

    current_running_apps: Dict[str, StreamlitApp] = {}

    # number of successive check when there is not connection to the main app
    current_no_connection_check: int = 0

    check_is_running = False

    @classmethod
    def get_current_running_apps(cls) -> List[StreamlitApp]:
        return list(cls.current_running_apps.values())

    @classmethod
    def main_app_is_running(cls) -> bool:
        return cls.main_app_process is not None and cls.main_app_process.is_alive()

    @classmethod
    def create_or_get_app(cls, app_id: str) -> StreamlitApp:
        if app_id in cls.current_running_apps:
            return cls.current_running_apps[app_id]

        return cls._create_app(app_id)

    @classmethod
    def _create_app(cls, app_id: str) -> StreamlitApp:
        cls.start_streamlit_main_app()

        app = StreamlitApp(cls.get_main_app_port(), app_id, cls.main_app_token)
        cls.current_running_apps[app_id] = app

        return app

    @classmethod
    def delete_app(cls, app: StreamlitApp) -> None:
        if not app.app_id in cls.current_running_apps:
            raise Exception("App not found")

        del cls.current_running_apps[app.app_id]
        app.clean()

    @classmethod
    def start_streamlit_main_app(cls) -> None:
        if cls.main_app_is_running():
            Logger.debug("Streamlit main app is already running")
            return

        cls.main_app_token = StringHelper.generate_random_chars(50)
        Logger.debug("Starting streamlit app")

        theme = cls.get_current_user_theme()

        cmd = ['streamlit', 'run', cls.MAIN_APP_FILE_PATH,
               '--theme.backgroundColor', theme.background_color,
               '--theme.secondaryBackgroundColor', theme.secondary_background_color,
               '--theme.textColor', theme.text_color,
               '--theme.primaryColor', theme.primary_color,
               '--server.port', str(cls.get_main_app_port()),
               # prevent streamlit to open the browser
               '--server.headless', "true",
               #    '--theme.font', 'Roboto Serif',
               # custom options
               '--',
               # configure a token to secure the app
               '--gws_token', cls.main_app_token]

        cls.main_app_process = SysProc.popen(cmd)
        cls.current_no_connection_check = 0
        cls.current_running_apps = {}

        try:
            cls.wait_main_app_heath_check()
        except Exception as e:
            Logger.error("Error while starting streamlit app, killing the process")
            cls.stop_main_app()
            raise e

        # start the check running in new thread
        cls.start_check_running()

    @classmethod
    def stop_main_app(cls) -> None:
        if cls.main_app_process is not None:
            cls.main_app_process.kill()
            cls.main_app_process = None
            cls.main_app_token = None

        cls.current_running_apps = {}
        cls.current_no_connection_check = 0

    @classmethod
    def start_check_running(cls) -> None:
        """
        Method to start the check running loop to check if the app is still used
        """
        if cls.check_is_running:
            return

        cls.check_is_running = True
        Thread(target=cls._check_running_loop).start()

    @classmethod
    def _check_running_loop(cls) -> None:
        while cls.main_app_is_running():
            time.sleep(cls.CHECK_RUNNING_INTERVAL)
            Logger.debug("Checking running streamlit app")

            try:
                if not cls._check_running():
                    break
            except Exception as e:
                Logger.error(f"Error while checking running streamlit app: {e}")

        Logger.debug("Killing the streamlit app")
        apps = list(cls.current_running_apps.values())
        for app in apps:
            cls.delete_app(app)
        cls.stop_main_app()

        cls.check_is_running = False

    @classmethod
    def _check_running(cls) -> bool:
        # count the number of network connections of the app
        connection_count = cls.count_connections()

        Logger.debug(f"Streamlit main app has {connection_count} connections")
        if connection_count <= 0:
            # if connection_count <= 0 or connection_count < app.default_number_of_connection:
            cls.current_no_connection_check += 1

            if cls.current_no_connection_check >= cls.SUCCESSIVE_CHECK_BEFORE_KILL:
                Logger.debug("No connections, killing the app")
                return False

        else:
            cls.current_no_connection_check = 0

        return True

    @classmethod
    def wait_main_app_heath_check(cls) -> None:
        # wait until ping http://localhost:8080/healthz  returns 200
        i = 0
        while True:
            time.sleep(1)

            health_check = cls.call_health_check()
            if health_check:
                break
            Logger.debug("Waiting for streamlit app to start")
            i += 1
            if i > 30:
                raise Exception("Streamlit app did not start in time")

    @classmethod
    def call_health_check(cls) -> bool:
        try:
            ExternalApiService.get(f"http://localhost:{cls.get_main_app_port()}/healthz")
        except Exception:
            return False

        return True

    @classmethod
    def count_connections(cls) -> int:
        if not cls.main_app_process:
            return 0

        # get the list of the connections
        connections = psutil.net_connections(kind='inet')

        # count the number of connections
        cons = []
        count_established = 0
        count_listen = 0
        for conn in connections:
            if conn.pid == cls.main_app_process.pid:
                if conn.status == 'ESTABLISHED':
                    count_established += 1
                elif conn.status == 'LISTEN':
                    count_listen += 1
                cons.append(conn)

        # specific case on the first apps, it seems to have only one established connection
        if count_established == 1:
            return count_established

        # to count otherwise, we substract the listen connections, if lower than 0, we return 0
        count = count_established - count_listen
        return count if count > 0 else 0

    ############################# OTHERS ####################################

    @classmethod
    def get_status_dto(cls) -> StreamlitStatusDTO:
        return StreamlitStatusDTO(
            status="RUNNING" if cls.main_app_is_running() else "STOPPED",
            running_apps=[app.to_dto() for app in cls.get_current_running_apps()],
            nb_of_connections=cls.count_connections(),
        )

    @classmethod
    def get_main_app_port(cls) -> int:
        return Settings.get_streamlit_main_app_port()

    @classmethod
    def get_current_user_theme(cls) -> FrontTheme:
        user = CurrentUserService.get_current_user()

        if user and user.has_dark_theme():
            return FrontService.get_dark_theme()

        return FrontService.get_light_theme()
