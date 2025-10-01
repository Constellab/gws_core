

from multiprocessing import Process
from time import sleep

import requests

from gws_core.app import App
from gws_core.core.utils.settings import Settings


class TestStartUvicornApp():
    """ Context to support with statement start the uvicorn api server in tests.
    It automatically starts the server when entering the context and stops it when exiting.
    """

    process: Process = None

    def enter(self):
        self.__enter__()

    def exit(self, exc_type, exc_value, traceback):
        self.__exit__(exc_type, exc_value, traceback)

    def __enter__(self):
        # Registrer the lab start. Use a new thread to prevent blocking the start
        self.process = Process(target=App.start_uvicorn_app)
        self.process.start()

        health_check_route = f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/health-check"

        # Wait for the server to start
        i = 0
        while i < 10:
            try:
                response = requests.get(health_check_route, timeout=1)
                if response.status_code == 200:
                    return
            except Exception:
                pass
            i += 1
            sleep(1)

        raise Exception("Server not started")

    def __exit__(self, exc_type, exc_value, traceback):
        # force kill the thread
        self.process.terminate()

        # raise the exception if exists
        if exc_value:
            raise exc_value
