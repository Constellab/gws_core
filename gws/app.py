# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import uvicorn
import importlib
import inspect 
import urllib

from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, FastAPI, status
from fastapi.responses import Response, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from gws.utils import slugify
from gws.settings import Settings
from gws.model import Study, User
from gws.logger import Error, Info
from gws.system import Monitor
from gws.queue import Queue

from ._app.core_app import *
from ._app.central_app import *

brick = "gws"
app = FastAPI(docs_url=None)

####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################

@app.on_event("startup")
async def startup_event():
    settings = Settings.retrieve()
    Info("GWS application started!", stdout=True)
    Info("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")), stdout=True)
    Info("* HTTP connection: https://{}:{} (in {} mode)".format(
        settings.get_data("app_host"), 
        settings.get_data("app_port"),
        ("prod" if settings.is_prod else "dev")
    ), stdout=True)
    Info("* Lab token: {}".format(
        urllib.parse.quote(settings.get_data("token"), safe='')
    ), stdout=True)

@app.on_event("shutdown")
async def shutdown_event():
    Queue.deinit()

####################################################################################
#
# App class
#
####################################################################################

class BaseApp:
    routes = []
    on_startup = []
    on_shutdown = []

    @classmethod
    def init(cls):
        pass

_settings = Settings.retrieve()
class App(BaseApp):
    """
    Base App
    """
    
    app: FastAPI = app
    is_running = False

    @classmethod
    def init(cls):
        """
        Initialize static routes
        """
        
        from ._sphynx.docgen import docgen
        from .service.model_service import ModelService

        # create default study and users
        Study.create_default_instance()
        User.create_owner_and_sysuser()

        # register all processes and resources
        ModelService.register_all_processes_and_resources()
        ModelService.create_model_tables()
        
        # start system monitoring
        Monitor.init(daemon=False)
        Queue.init(daemon=False)
        
        # static dirs and docs
        dirs = _settings.get_dependency_dirs()
        for name in dirs:
            static_dir = os.path.join(dirs["gws"], "index/static/")
            if os.path.exists(os.path.join(static_dir)):
                app.mount(f"/static/{name}/", StaticFiles(directory=static_dir), name=f"/static/{name}")
        
            html_dir = os.path.join(dirs[name],"./docs/html/build")
            if not os.path.exists(os.path.join(html_dir,"index.html")):
                #os.makedirs(html_dir)
                docgen(name, dirs[name], _settings, force=True)
            app.mount(f"/docs/{name}/", StaticFiles(directory=html_dir), name=f"/docs/{name}/")

        # api routes
        app.mount("/core-api/", core_app)
        app.mount("/central-api/", central_app)

    @classmethod 
    def start(cls):
        """
        Starts FastAPI uvicorn
        """
        settings = Settings.retrieve()
        settings.set_data("app_host","0.0.0.0")
        settings.save()
        
        cls.init()
        uvicorn.run(cls.app, host=settings.get_data("app_host"), port=int(settings.get_data("app_port")))
        cls.is_running = True
