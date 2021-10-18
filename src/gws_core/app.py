# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette_context.middleware.context_middleware import ContextMiddleware

from ._core_app_importer import *
from .central.central_app import central_app
from .core.classes.cors_config import CorsConfig
from .core.utils.logger import Logger
from .core.utils.settings import Settings
from .core.utils.utils import Utils
from .core_app import core_app
from .experiment.queue_service import QueueService
from .lab.monitor import Monitor
from .lab.system_service import SystemService

app = FastAPI(docs_url=None)

####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################


@app.on_event("startup")
async def startup():
    """ Called before the app is started """

    App.init()


@app.on_event("shutdown")
async def shutdown():
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
        Monitor.init(daemon=True)
        QueueService.init(daemon=True)

    @classmethod
    def deinit(cls):
        """
        Deinitialize the app
        """

        Monitor.deinit()
        QueueService.deinit()
        cls.is_running = False

    @classmethod
    def start(cls, ip: str = "0.0.0.0", port: int = 3000):
        """
        Starts FastAPI uvicorn
        """

        SystemService.init()

        # Add static dirs for docs of git modules
        # @ToDo: Add route or hooks to compile docs after
        settings: Settings = Settings.retrieve()
        brick_paths = Utils.get_all_brick_paths()
        Logger.info(
            f"Starting server in {('prod' if settings.is_prod else 'dev')} mode ...")
        for path in brick_paths:
            name = path.strip("/").split("/")[-1]
            documention_path = os.path.join(path, "./docs/html/build")
            if not os.path.exists(documention_path):
                os.makedirs(documention_path)
            cls.app.mount(
                f"/docs/{name}/", StaticFiles(directory=documention_path), name=f"/docs/{name}/")

        # Configure the CORS
        CorsConfig.configure_app_cors(app)

        # configure the context middleware
        cls.app.add_middleware(
            ContextMiddleware
        )

        # api routes
        cls.app.mount("/core-api/", core_app)
        cls.app.mount("/central-api/", central_app)

        uvicorn.run(cls.app, host=ip, port=int(port))
