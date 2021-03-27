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

from gws.base import slugify
from gws.settings import Settings
from gws.model import Study
from gws.user import User
from gws.controller import Controller
#from gws.central import Central
from gws.logger import Error

brick = "gws"
app = FastAPI(docs_url=None)

####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################

@app.on_event("startup")
async def startup_event():
    Study.create_default_instance()
    User.create_owner()

    settings = Settings.retrieve()
    print("GWS application started!")
    print("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))

    print("* HTTP connection: https://{}:{}".format(
        settings.get_data("app_host"), 
        settings.get_data("app_port")
    ))

    print("* Lab token: {}".format(
        urllib.parse.quote(settings.get_data("token"), safe='')
    ))

@app.on_event("shutdown")
async def shutdown_event():
    pass

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
    ctrl = Controller
    debug = _settings.get_data("is_test") or _settings.get_data("is_demo")
    is_running = False

    @classmethod
    def init(cls):
        """
        Intialize static routes
        """
        
        from ._sphynx.docgen import docgen
        from ._api.api import app as core_app
        
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
        app.mount("/api/", core_app)

    @classmethod 
    def start(cls):
        """
        Starts FastAPI uvicorn
        """
        settings = Settings.retrieve()
        settings.set_data("app_host","0.0.0.0")
        settings.save()
        uvicorn.run(cls.app, host=settings.get_data("app_host"), port=int(settings.get_data("app_port")))
        cls.is_running = True
