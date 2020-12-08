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
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
import jinja2

from gws.base import slugify
from gws.settings import Settings
from gws.model import User
from gws.controller import Controller
from gws.central import Central
from gws.logger import Logger

from gws._auth.user import check_authenticate_user



brick = "gws"
app = FastAPI(docs_url="/apidocs")

def get_template_env(settings):
    """
    Get Jinj2 template environment
    """
    paths = []
    for k in settings.get_dependency_names():
        p = settings.get_page_dir(k)
        if p is None:
            Logger.error(Exception(f"The page dir of the brick '{k}' is None"))

        paths.append(p)

    return jinja2.Environment(loader=jinja2.FileSystemLoader(paths))

def page_exists(page,brick=brick):
    """
    Get Jinj2 template environment
    """
    settings = Settings.retrieve()
    template_dir = settings.get_page_dir(brick)
    if not template_dir is None:
        return os.path.exists(os.path.join(template_dir,page+".html"))
    else:
        return False

@app.get("/")
#async def display_html_home_page(_: bool = Depends(check_authenticate_user)):
async def show_home_page():
    return RedirectResponse(url=f'/page/{brick}')

@app.api_route("/page/{brick_name}", response_class=HTMLResponse, methods=["GET", "POST"])
@app.api_route("/page/{brick_name}/{entry_name}", response_class=HTMLResponse, methods=["GET", "POST"])
@app.api_route("/page/{brick_name}/{entry_name}/{action_name}", response_class=HTMLResponse, methods=["GET", "POST"])
async def show_brick_page(request: Request, brick_name: Optional[str] = "gws", entry_name: Optional[str] = 'index', action_name: Optional[str] = 'index') :
    brick_app_module = importlib.import_module(f"{brick_name}.app")
    page_t = getattr(brick_app_module, "Page", None)
    
    try:
        entry_name = slugify(entry_name,snakefy=True).strip("_")
        action_name = slugify(action_name,snakefy=True).strip("_")
        func_name = entry_name + "_" + action_name
        async_func = getattr(page_t, func_name, None)
        results = await async_func(request)
        status = True
        message = ""
    except Exception as err:
        status = False
        results = None
        message = f"{err}"

    settings = Settings.retrieve()
    css, js, module_js = settings.get_local_static_css_js()
    env = get_template_env(settings)
    template = env.get_template("gws/_index/index.html")
    html = template.render({
        'response': {"status": status, "results": results, "message": message},
        'settings': settings,
        'brick_name': brick_name,
        'entry_name': entry_name,
        'action_name': action_name,
        'request': request,
        'scripts':{
            "css": css,
            "js": js,
            "module_js": module_js
        }
    })

    return HTMLResponse(html)


@app.api_route("/api/{brick_name}/{api_func}", response_class=JSONResponse, methods=["GET", "POST"])
async def call_brick_api(request: Request, brick_name: Optional[str] = "gws", api_func: Optional[str] = None) :
    brick_app_module = importlib.import_module(f"{brick_name}.app")
    api_t = getattr(brick_app_module, "API", None)

    try:
        async_func = getattr(api_t, api_func.replace("-","_").lower(), None)
        results = await async_func(request)
        return {"status": True, "results": results, "message": ""}
    except Exception as err:
        return {"status": False, "results": {}, "message": f"{err}"}


####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################

@app.on_event("startup")
async def startup_event():
    Central.put_status(is_running=True)

    settings = Settings.retrieve()
    print("GWS application started!")
    print("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))

    print("* HTTP connection: http://{}:{}/demo".format(
        settings.get_data("app_host"), 
        settings.get_data("app_port")
    ))

    print("* Lab token: {}".format(
        urllib.parse.quote(settings.get_data("token"), safe='')
    ))

@app.on_event("shutdown")
async def shutdown_event():
    Central.put_status(is_running=False)

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

        # automatic static dirs
        dirs = _settings.get_dependency_dirs()
        for name in dirs:
            k = f"/static-{name}"
            app.mount(k, StaticFiles(directory=os.path.join(dirs[name],"./web/static")), name=k)

        # manual static dirs
        statics = _settings.get_static_dirs()
        for k in statics:
            app.mount(k, StaticFiles(directory=statics[k]), name=k)

        from gws._app.central import central_app
        from gws._app.core import core_app
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