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
from fastapi.responses import Response, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from pydantic import BaseModel

from gws.settings import Settings
from gws.model import User
from gws.controller import Controller
from gws.central import Central


from gws._auth.user import check_authenticate_user

brick = "gws"
app = FastAPI(docs_url="/api-docs")

####################################################################################
#
# Page endpoints
#
####################################################################################

def get_templates(brick=brick):
    settings = Settings.retrieve()
    template_dir = settings.get_page_dir(brick)
    if not template_dir is None:
        return Jinja2Templates(directory=template_dir), settings
    else:
        return None

def page_exists(page,brick=brick):
    settings = Settings.retrieve()
    template_dir = settings.get_page_dir(brick)
    if not template_dir is None:
        return os.path.exists(os.path.join(template_dir,page+".html"))
    else:
        return False

@app.get("/")
#async def display_html_home_page(_: bool = Depends(check_authenticate_user)):
async def display_html_home_page():
    return RedirectResponse(url=f'/page/{brick}')

@app.get("/page/{brick}/", response_class=HTMLResponse)
@app.get("/page/{brick}/{page}", response_class=HTMLResponse)
async def display_html_brick_page(request: Request, brick, page: Optional[str] = 'index', only_inner_html: Optional[str] = None) :
    if only_inner_html == "true":
        #run brick endpoints
        brick_app = importlib.import_module(f"{brick}.app")
        async_func = getattr(brick_app, page.lower() + "_page", None)
        if inspect.iscoroutinefunction(async_func):
            try:
                response = await async_func(request)
            except:
                response = None
        else:
            response = None

        if isinstance(response, Response):
            return response
        else:
            templates, settings = get_templates(brick)
            return templates.TemplateResponse(f"{page}.html", {
                'data': response,
                'settings': settings,
                'request': request,
            })
    else:
        if not page_exists(page,brick):
            raise HTTPException(
                status_code=404,
                detail="Page not found",
                headers={"X-Error": "Page not found"},
            )
        else:
            templates, settings = get_templates()
            return templates.TemplateResponse("index/index.html", {
                'settings': settings,
                'page': page,
                'brick': brick,
                'request': request,
            })

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
        # static dirs
        statics = _settings.get_static_dirs()
        for k in statics:
            app.mount(k, StaticFiles(directory=statics[k]), name=k)

        from gws._app.central import central_app
        from gws._app.prism import prism_app
        app.mount("/central/api", central_app)
        app.mount("/prism/api", prism_app)

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

