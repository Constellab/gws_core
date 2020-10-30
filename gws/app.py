# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import uvicorn
import importlib
import inspect 

from typing import Optional

from fastapi import Depends, Form, HTTPException, Request, FastAPI
from fastapi.routing import APIRoute as Route, Mount
from fastapi.responses import Response, JSONResponse, PlainTextResponse,  FileResponse,  HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware import Middleware
from pydantic import BaseModel

from fastapi.security import OAuth2PasswordBearer

from gws.settings import Settings
from gws.view import HTMLViewTemplate, JSONViewTemplate, PlainTextViewTemplate
from gws.model import Resource, HTMLViewModel, JSONViewModel, User
from gws.controller import Controller
from gws.central import Central

####################################################################################
#
# Endpoints
#
####################################################################################

brick = "gws"
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def decode_token(token):
    settings = Settings.retrieve()
    if settings.get_data("token") == token:
        pass
    else:
        pass

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_token(token)
    return user

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

# PRISM action

class _ViewModel(BaseModel):
    uri: str
    data: dict

@app.get("/api/prism/{uri}")
async def get_vmodel(uri: str) -> (dict, str,):
    """
    Get and render a ViewModel
    """

    try:
        vmodel = Controller.action("get", uri)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }

@app.post("/api/prism/")
async def post_vmodel(vmodel: _ViewModel) -> (dict, str,):
    """
    Post an render a ViewModel
    """

    try:
        vmodel = Controller.action("post", uri=vmodel.uri, data=vmodel.data)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }

@app.put("/api/prism/")
async def put_vmodel(vmodel: _ViewModel) -> (dict, str,):
    """
    Post and render a ViewModel
    """

    try:
        vmodel = Controller.action("put", uri=vmodel.uri, data=vmodel.data)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }

@app.delete("/api/prism/{uri}/")
async def delete_vmodel(uri: str) -> (dict, str,):
    """
    Post a ViewModel and render its
    """

    try:
        vmodel = Controller.action("delete", uri)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }


# API

# Lab instance

@app.get("/api/lab-instance/")
async def get_lab_instance_status():
    from gws.lab import Lab
    return { "status": True, "response" : Lab.get_status() }

# User

class _User(BaseModel):
    uri: str
    token: str

@app.post("/api/user/create")
async def create_user(user: _User):
    try:
        tf = Central.create_user(user.dict())
        return { "status": tf, "response" : "" }
    except Exception as err:
        return { "status": False, "response": str(err) }

@app.get("/api/user/{user_uri}")
async def get_user(user_uri : str):
    try:
        user_dict = Central.get_user_status(user_uri)
        return { "status": True, "response" : user_dict }
    except Exception as err:
        return { "status": False, "response" : str(err) }

@app.get("/api/user/{user_uri}/activate")
async def activate_user(user_uri : str):
    try:
        tf = Central.activate_user(user_uri)
        return { "status": tf, "response" : "" }
    except Exception as err:
        return { "status": False, "response" : str(err) }

@app.get("/api/user/{user_uri}/deactivate")
async def deactivate_user(user_uri : str):
    try:
        tf = Central.deactivate_user(user_uri)
        return { "status": tf, "response" : "" }
    except Exception as err:
        return { "status": False, "response" : str(err) }


# Experiment
class _Experiment(BaseModel):
    uri: str
    protocol: str
    
@app.put("/api/experiment/open")
async def open_experiment_or_create_if_not_exists(exp: _Experiment):
    try:
        tf = Central.create_experiment(exp.dict())
        return { "status": tf, "response" : "" }
    except Exception as err:
        return { "status": False, "response": str(err) }

@app.put("/api/experiment/{experiment_uri}/close")
async def close_experiment(request):
    return { "status": True, "response" : ""}

@app.delete("/api/experiment/{experiment_uri}")
async def delete_experiment(request):
    return { "status": True, "response" : ""}

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
        Defines the web routes of the brick.

        Routing coventions: 
        
        To prevent route collisions, it is highly recommended to 
        prefix route names of the name of the current brick.
        For example: 
        * /<brick name>/home/       -> home page route
        * /<brick name>/settings/   -> setting page route
        """

        # static dirs
        statics = _settings.get_static_dirs()
        print(statics)
        for k in statics:
            app.mount(k, StaticFiles(directory=statics[k]), name=k)

        #misc
        cls.on_startup.append(cls._on_startup)
        cls.on_shutdown.append(cls._on_shutdown)
    
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

    @classmethod 
    def _on_startup(cls):
        """
        Called on application startup to create test objects
        """

        Central.put_status(is_running=True)
        
        settings = Settings.retrieve()
        from gws.robot import Robot, HTMLRobotViewModel, JSONRobotViewModel

        try:
            robot = Robot.get( Robot.id==1 )
            html_vmodel = HTMLRobotViewModel.get( HTMLRobotViewModel.id == 1 )
        except:
            robot = Robot()
            robot.data["name"] = "R. Giskard Reventlov"
            robot.save()
            html_vmodel = HTMLRobotViewModel(robot)
            html_vmodel.save()
            json_vmodel = JSONRobotViewModel(robot)
            json_vmodel.save()
        
        import urllib
        print("GWS application started!")
        print("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))

        if settings.get_data("is_demo"):
            print("* HTTP connection: http://{}:{}/demo".format(
                settings.get_data("app_host"), 
                settings.get_data("app_port")
            ))
        else:
            print("* HTTP connection: http://{}:{}/login?token={}".format(
                settings.get_data("app_host"), 
                settings.get_data("app_port"), 
                urllib.parse.quote(settings.get_data("token"), safe='')
            ))
            print("* Token: {}".format(
                urllib.parse.quote(settings.get_data("token"), safe='')
            ))

    @classmethod 
    def _on_shutdown(cls):
        Central.put_status(is_running=False)

