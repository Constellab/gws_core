# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ._sphynx.docgen import docgen
from .central.central_app import central_app
from .core.model.study import Study
from .core.utils.logger import Logger
from .core.utils.settings import Settings
from .core_app import core_app
from .experiment.queue import Queue
from .lab.system import Monitor
from .model.model_service import ModelService
from .user.user_service import UserService

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

    @classmethod
    def init(cls):
        """
        Initialize the app
        """

        Monitor.init(daemon=True)
        Queue.init(daemon=True, verbose=False)

    @classmethod
    def deinit(cls):
        """
        Deinitialize the app
        """

        Monitor.deinit()
        Queue.deinit()

    @classmethod
    def start(cls, ip: str = "0.0.0.0", port: int = 3000):
        """
        Starts FastAPI uvicorn
        """

        ModelService.create_tables()
        ModelService.register_all_processes_and_resources()
        Study.create_default_instance()
        UserService.create_owner_and_sysuser()

        # static dirs and docs
        settings = Settings.retrieve()
        dirs = settings.get_dependency_dirs()
        Logger.info(
            f"Starting server in {('prod' if settings.is_prod else 'dev')} mode ...")
        for name in dirs:
            html_dir = os.path.join(dirs[name], "./docs/html/build")
            if not os.path.exists(os.path.join(html_dir, "index.html")):
                # os.makedirs(html_dir)
                docgen(name, dirs[name], settings, force=True)
            cls.app.mount(
                f"/docs/{name}/", StaticFiles(directory=html_dir), name=f"/docs/{name}/")
        # api routes
        cls.app.mount("/core-api/", core_app)
        cls.app.mount("/central-api/", central_app)
        uvicorn.run(cls.app, host=ip, port=int(port))
