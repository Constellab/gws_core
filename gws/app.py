# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import uvicorn
import importlib
import inspect 
import urllib

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Form, HTTPException, Request, FastAPI, status
from fastapi.routing import APIRoute as Route, Mount
from fastapi.responses import Response, JSONResponse, PlainTextResponse,  FileResponse,  HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware import Middleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from pydantic import BaseModel

from passlib.context import CryptContext

from gws.settings import Settings
from gws.view import HTMLViewTemplate, JSONViewTemplate, PlainTextViewTemplate
from gws.model import Resource, HTMLViewModel, JSONViewModel, User
from gws.controller import Controller
from gws.central import Central

brick = "gws"
app = FastAPI()


####################################################################################
#
# Login
#
####################################################################################

from gws._auth import _Token
from gws._auth import    login_for_access_token as auth_login_for_access_token, \
                        get_current_active_user as auth_get_current_active_user

@app.post("/handshake", response_model=_Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return await auth_login_for_access_token(form_data)

# User
class _User(BaseModel):
    uri: str
    token: str

@app.get("/me/", response_model=_User)
async def read_users_me(current_user: _User = Depends(auth_get_current_active_user)):
    return current_user

####################################################################################
#
# Endpoints
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

@app.get("/api/prism/{rtype}/{uri}")
async def get_vmodel(rtype: str, uri: str) -> (dict, str,):
    """
    Get and render a ViewModel
    """

    try:
        vmodel = Controller.action(action="get", rtype=rtype, uri=uri)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }

@app.post("/api/prism/")
async def post_vmodel(rtype: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post an render a ViewModel
    """

    try:
        vmodel = Controller.action(action="post", rtype=rtype, uri=vmodel.uri, data=vmodel.data)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }

@app.put("/api/prism/{rtype}/")
async def put_vmodel(rtype: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post and render a ViewModel
    """

    try:
        vmodel = Controller.action(action="put", rtype=rtype, uri=vmodel.uri, data=vmodel.data)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }

@app.delete("/api/prism/{rtype}/{uri}/")
async def delete_vmodel(rtype: str, uri: str) -> (dict, str,):
    """
    Post a ViewModel and render its
    """

    try:
        vmodel = Controller.action(action="delete", rtype=rtype, uri=uri)
    except Exception as err:
        return {"status": False, "reponse": f"{err}"}

    return { "status": True, "reponse": vmodel.render() }


# API

# Lab instance

@app.get("/api/lab-instance/")
async def get_lab_instance_status():
    from gws.lab import Lab
    return { "status": True, "response" : Lab.get_status() }

@app.post("/api/user/create")
async def create_user(user: _User):
    try:
        user_dict = Central.create_user(user.dict())
        return { "status": True, "response" : user_dict }
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
class _Protocol(BaseModel):
    uri: str
    graph: Optional[dict] = None

class _Experiment(BaseModel):
    uri: str
    protocol: _Protocol
    
@app.post("/api/experiment/create")
async def create_experiment(exp: _Experiment):
    try:
        exp = Central.create_experiment(exp.dict())
        return { 
            "status": True, 
            "response" : {
                "experiment": {
                    "uri": exp.uri
                },
                "protocol": {
                    "uri": exp.protocol.uri
                }
            }
        }
    except Exception as err:
        return { "status": False, "response": str(err) }

@app.put("/api/experiment/{experiment_uri}/close")
async def close_experiment(request):
    return { "status": True, "response" : ""}

@app.delete("/api/experiment/{experiment_uri}")
async def delete_experiment(request):
    return { "status": True, "response" : ""}

# Protocol

@app.get("/api/protocol/{protocol_uri}")
async def get_protocol(protocol_uri: str):
    try:
        proto_dict = Central.get_protocol(protocol_uri)
        return { "status": True, "response" : proto_dict }
    except Exception as err:
        return { "status": False, "response" : str(err) }

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

