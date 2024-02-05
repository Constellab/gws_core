# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import time
from threading import Thread
from typing import Dict, List

import psutil

from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.string_helper import StringHelper
from gws_core.streamlit.streamlit_app import StreamlitApp


class StreamlitAppManager():
    """Class to manage the different streamlit apps

    Each apps runs on the same streamlit server managed by the _main_streamlit_app
    """

    MAIN_APP_PORT = 8501

    # interval in second to check if the app is still used
    CHECK_RUNNING_INTERVAL = 5

    # number of successive check before killing the app
    SUCCESSIVE_CHECK_BEFORE_KILL = 3

    MAIN_APP_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "_main_streamlit_app.py")

    main_app_token: str = None
    main_app_process: SysProc = None

    current_running_apps: Dict[str, StreamlitApp] = {}

    current_no_connection_check: int = 0

    check_is_running = False

    @classmethod
    def get_current_running_apps(cls) -> List[StreamlitApp]:
        return list(cls.current_running_apps.values())

    @classmethod
    def main_app_is_running(cls) -> bool:
        return cls.main_app_process is not None

    @classmethod
    def create_or_get_app(cls, resource_id: str) -> StreamlitApp:
        if resource_id in cls.current_running_apps:
            return cls.current_running_apps[resource_id]

        return cls._create_app(resource_id)

    @classmethod
    def _create_app(cls, resource_id: str) -> StreamlitApp:
        cls.start_streamlit_main_app()

        app = StreamlitApp(cls.MAIN_APP_PORT, resource_id, cls.main_app_token)
        cls.current_running_apps[resource_id] = app

        return app

    @classmethod
    def delete_app(cls, app: StreamlitApp) -> None:
        if not app.resource_id in cls.current_running_apps:
            raise Exception("App not found")

        del cls.current_running_apps[app.resource_id]
        app.clean()

    @classmethod
    def start_streamlit_main_app(cls) -> None:
        if cls.main_app_is_running():
            Logger.debug("Streamlit main app is already running")
            return

        cls.main_app_token = StringHelper.generate_random_chars(50)
        Logger.debug(f"Starting streamlit app")

        cmd = ['streamlit', 'run', cls.MAIN_APP_FILE_PATH,
               '--theme.backgroundColor', '#222222',
               '--theme.secondaryBackgroundColor', '#2B2D2E',
               '--theme.textColor', '#ffffff',
               '--theme.primaryColor', '#49A8A9',
               '--server.port', str(cls.MAIN_APP_PORT),
               #    '--theme.font', 'Roboto Serif',
               '--',
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
                cls._check_running()
            except Exception as e:
                Logger.error(f"Error while checking running streamlit app: {e}")

        cls.check_is_running = False

    @classmethod
    def _check_running(cls) -> None:
        if not cls.main_app_is_running():
            return

        # count the number of network connections of the app
        connection_count = cls.count_connections()

        Logger.debug(f"Streamlit main app has {connection_count} connections")
        if connection_count <= 0:
            # if connection_count <= 0 or connection_count < app.default_number_of_connection:
            cls.current_no_connection_check += 1

            if cls.current_no_connection_check >= cls.SUCCESSIVE_CHECK_BEFORE_KILL:
                Logger.debug("No connection to the streamlit app, killing the process")
                apps = list(cls.current_running_apps.values())
                for app in apps:
                    cls.delete_app(app)

                cls.stop_main_app()

        else:
            cls.current_no_connection_check = 0

    @classmethod
    def wait_main_app_heath_check(cls) -> None:
        # wait until ping http://localhost:8080/healthz  returns 200
        i = 0
        while True:
            time.sleep(1)
            try:
                ExternalApiService.get(f"http://localhost:{cls.MAIN_APP_PORT}/healthz")
                break
            except Exception:
                Logger.debug("Waiting for streamlit app to start")
                i += 1
                if i > 30:
                    raise Exception("Streamlit app did not start in time")

    @classmethod
    def count_connections(cls) -> int:

        # get the list of the connections
        connections = psutil.net_connections(kind='inet')

        # count the number of connections
        cons = []
        count = 0
        for conn in connections:
            if conn.pid == cls.main_app_process.pid:
                if conn.status == 'ESTABLISHED':
                    count += 1
                elif conn.status == 'LISTEN':
                    count -= 1
                cons.append(conn)

        return count
