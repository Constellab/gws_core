# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from threading import Thread

import uvicorn
from fastapi import FastAPI
from starlette_context.middleware.context_middleware import ContextMiddleware

from .core.classes.cors_config import CorsConfig
from .core_app import core_app
from .lab.system_service import SystemService
from .space.space_app import space_app

app = FastAPI(docs_url=None)

####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################


@app.on_event("startup")
def startup():
    """ Called before the app is started """

    App.init()


@app.on_event("shutdown")
def shutdown():
    """ Called before the application is stopped """

    App.deinit()

####################################################################################
#
# App class
#
####################################################################################


class App:
    """
    Base App
    """

    app: FastAPI = app
    is_running: bool = False

    @classmethod
    def init(cls):
        """
        Initialize the app
        """

        cls.is_running = True
        SystemService.init_queue_and_monitor()

    @classmethod
    def deinit(cls):
        """
        Deinitialize the app
        """

        SystemService.deinit_queue_and_monitor()
        cls.is_running = False

    @classmethod
    def start(cls, port: int = 3000):
        """
        Starts FastAPI uvicorn
        """

        SystemService.migrate_db()
        SystemService.init()

        # Configure the CORS
        CorsConfig.configure_app_cors(app)

        # configure the context middleware
        cls.app.add_middleware(
            ContextMiddleware
        )

        # Registrer the lab start. Use a new thread to prevent blocking the start
        th = Thread(target=SystemService.register_lab_start)
        th.start()

        # api routes
        cls.app.mount("/core-api/", core_app)
        # TODO To remove once central uses space-api (we can do that once all lab are on v0.5.0)
        cls.app.mount("/central-api/", space_app)
        cls.app.mount("/space-api/", space_app)

        uvicorn.run(cls.app, host='0.0.0.0', port=int(port))
