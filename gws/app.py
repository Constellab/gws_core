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
from fastapi.requests import Request
from pydantic import BaseModel

from gws.base import slugify
from gws.settings import Settings
from gws.model import Study
from gws.user import User
from gws.controller import Controller
#from gws.central import Central
from gws.logger import Error

from gws._auth.user import check_authenticate_user

brick = "gws"
app = FastAPI(docs_url="/apidocs")

@app.api_route("/brick-api/{brick_name}/{api_func}", response_class=JSONResponse, methods=["GET", "POST"])
async def call_brick_api(request: Request, brick_name: Optional[str] = "gws", api_func: Optional[str] = None) :
    brick_app_module = importlib.import_module(f"{brick_name}.app")
    api_t = getattr(brick_app_module, "API", None)

    try:
        async_func = getattr(api_t, api_func.replace("-","_").lower(), None)
        results = await async_func(request)
        return results
    except Exception as err:
        raise Error("gws.app", "call_brick_api", f"{err}")
        #return {"status": False, "results": {}, "message": f"{err}"}

####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################

@app.on_event("startup")
async def startup_event():
    Study.create_default_instance()
    User.create_owner()
    #Central.put_status(is_running=True)

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
    #Central.put_status(is_running=False)
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
        from ._app.central import central_app
        from ._app.core import core_app
        
        # static dirs and docs
        dirs = _settings.get_dependency_dirs()
        for name in dirs:
            static_dir = os.path.join(dirs["gws"], "index/static/")
            if os.path.exists(os.path.join(static_dir)):
                app.mount(f"/static/{name}/", StaticFiles(directory=static_dir), name=f"/static/{name}")
        
            html_dir = os.path.join(dirs[name],"./docs/html/build")
            if not os.path.exists(os.path.join(html_dir,"index.html")):
                docgen(name, dirs[name], _settings, force=True)
            app.mount(f"/docs/{name}/", StaticFiles(directory=html_dir), name=f"/docs/{name}/")

        # api routes
        app.mount("/central-api/", central_app)
        app.mount("/core-api/", core_app)

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
