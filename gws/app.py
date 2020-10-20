# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import uvicorn

from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse, PlainTextResponse,  FileResponse,  HTMLResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.endpoints import HTTPEndpoint, WebSocketEndpoint
from starlette.authentication import requires
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from gws.settings import Settings
from gws.view import HTMLViewTemplate, JSONViewTemplate, PlainTextViewTemplate
from gws.model import Resource, HTMLViewModel, JSONViewModel, User
from gws.controller import Controller
from gws.central import Central
from gws._app import auth, demo


####################################################################################
#
# Endpoints
#
####################################################################################

def get_templates():
    settings = Settings.retrieve()
    template_dir = settings.get_template_dir("gws")
    return Jinja2Templates(directory=template_dir), settings

async def not_found(request, exc):
    templates, settings = get_templates()
    return templates.TemplateResponse("error/404.html", {
        'request': request, 
        'settings': settings,
        'exception': exc
    }, status_code=404)

async def server_error(request, exc):
    templates, settings = get_templates()
    return templates.TemplateResponse("error/500.html", {
        'request': request, 
        'settings': settings,
        'exception': exc
    }, status_code=500)

@requires("authenticated")
async def hellopage(request):
    templates, settings = get_templates()
    return templates.TemplateResponse("hello.html", {
        'request': request, 
        'settings': settings,
    })

@requires("authenticated")
async def homepage(request):
    templates, settings = get_templates()
    return templates.TemplateResponse("index/index.html", {
        'request': request, 
        'settings': settings,
    })

@requires("authenticated")
async def settingpage(request):
    templates, settings = get_templates()
    return templates.TemplateResponse("settings.html", {
        'request': request, 
        'settings': settings,
    })

@requires("authenticated")
async def statuspage(request):
    from gws.lab import Lab
    return JSONResponse(Lab.get_status())

class HTTPApp(HTTPEndpoint):
    async def get(self, request):
        return await App.action(request)
    
    async def post(self, request):
        return await App.action(request)

# class WebSocketApp(WebSocketEndpoint):
#     encoding = 'bytes'

#     async def on_connect(self, websocket):
#         await websocket.accept()

#     async def on_receive(self, websocket, data):
#         vmodel = await App.action(websocket)
#         html = vmodel.render(request=websocket)
#         await websocket.send_bytes(b""+html)

#     async def on_disconnect(self, websocket, close_code):
#         pass

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
    

settings = Settings.retrieve()
class App(BaseApp):
    """
    Base App
    """

    app: Starlette = None
    ctrl = Controller
    middleware = [
        Middleware( 
            SessionMiddleware, 
            secret_key=settings.get_data("session_key"), 
            session_cookie="gws",
            max_age=60*60*24
        ),
        Middleware( 
            AuthenticationMiddleware, 
            backend = auth.AuthBackend()
        )
    ]
    debug = settings.get_data("is_test") or settings.get_data("is_demo")
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
        
        # process and resource routes
        cls.routes.append(Route('/{action}/{uri}/{data}/', HTTPApp))
        cls.routes.append(Route('/{action}/{uri}/', HTTPApp))

        # static dirs
        statics = settings.get_static_dirs()
        for k in statics:
            cls.routes.append(Mount(k, StaticFiles(directory=statics[k]), name=k))

        # settings
        cls.routes.append(Route("/settings/", settingpage))

        # hello
        cls.routes.append(Route("/hello/", hellopage))

        # demo
        cls.routes.append(Route('/demo/', endpoint=demo.demo))

        # auth
        cls.routes.append(Route('/login', endpoint=auth.loginpage, name="auth"))
        cls.routes.append(Route('/logout', endpoint=auth.logoutpage, name="auth"))
        cls.routes.append(Route('/profile', endpoint=auth.profilepage, name="auth"))

        # home
        cls.routes.append(Route("/", homepage))

        # api
        cls.routes.append(Route("/status", statuspage))

        #misc
        cls.on_startup.append(cls._on_startup)
        cls.on_shutdown.append(cls._on_shutdown)
    
    @classmethod
    async def action(cls, request) -> Response:
        """
        Deals a user action and returns a response
        :return: The response
        :rtype: `starlette.responses.Response`
        """
        vmodel = await Controller.action(request)
        rendering = vmodel.render(request=request)

        if isinstance(rendering, Response):
            return rendering
        else:
            if vmodel.template.is_html():
                return HTMLResponse(rendering)
            elif vmodel.template.is_json():
                return JSONResponse(rendering)
            else:
                return PlainTextResponse(rendering)

    @classmethod 
    def start(cls):
        """
        Starts the starlette uvicorn web application
        """

        settings = Settings.retrieve()
        exception_handlers = {
            404: not_found,
            500: server_error
        }

        # starlette
        cls.app = Starlette(
            debug=cls.debug, 
            routes=cls.routes, 
            middleware=cls.middleware, 
            on_startup=cls.on_startup,
            on_shutdown=cls.on_shutdown,
            exception_handlers=exception_handlers
        )

        uvicorn.run(cls.app, host=settings.get_data("app_host"), port=int(settings.get_data("app_port")))
        cls.is_running = True

    @classmethod 
    def _on_startup(cls):
        """
        Called on application startup to create test objects
        """
        Central.tell_is_running()
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
        Central.tell_is_stopped()

    @classmethod 
    def test(cls, url: str) -> Response:
        """
        Returns a response in test mode
        :param url: The test url
        :type url: str
        :return: The response
        :rtype: `starlette.responses.Response`
        """
        from starlette.testclient import TestClient
        client = TestClient(cls.app)
        response = client.get(url)
        return response

