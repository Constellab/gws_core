# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import base64
import binascii

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse, PlainTextResponse,  FileResponse,  HTMLResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.endpoints import HTTPEndpoint, WebSocketEndpoint

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser,
    AuthCredentials
)

from gws.settings import Settings
from gws.view import HTMLViewTemplate, JSONViewTemplate, PlainTextViewTemplate
from gws.model import Resource, HTMLViewModel, JSONViewModel, User
from gws.controller import Controller
from gws.logger import Logger

settings = Settings.retrieve()

####################################################################################
#
# Endpoints
#
####################################################################################

template_dir = settings.get_template_dir("gws")
templates = Jinja2Templates(directory=template_dir)

async def hello(request):
    return templates.TemplateResponse("hello/index.html", {
        'request': request, 
        'settings': settings,
    })

async def homepage(request):
    return templates.TemplateResponse("index/index.html", {
        'request': request, 
        'settings': settings,
    })

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

from gws._app import user as user_endpoint
from gws._app import demo as demo_endpoint

####################################################################################
#
# AuthBackend class
#
####################################################################################

class AuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as err:
            raise AuthenticationError(f'Invalid basic auth credentials. Error: {err}')

        email, _, password = decoded.partition(":")
        
        try:
            user = User.get(email=email, password=password)
        except:
            raise AuthenticationError('User not found')

        scopes = ["authenticated"]
        if user.is_admin:
            scopes.append("admin")

        auth_credentials = AuthCredentials(scopes)
        return auth_credentials, user

####################################################################################
#
# App class
#
####################################################################################

class App :
    """
    Base App
    """

    app: Starlette = None
    ctrl = Controller
    routes = []
    middleware = [
        Middleware( 
            SessionMiddleware, 
            secret_key=settings.get_data("secret_key"), 
            session_cookie="gws"
        ),
        Middleware( 
            AuthenticationMiddleware, 
            backend = AuthBackend()
        )
    ]
    debug = settings.get_data("is_test")
    is_running = False
    
    @classmethod
    def init_routes(cls):
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
        cls.routes.append(Route('/gws/{action}/{uri}/{data}/', HTTPApp))
        cls.routes.append(Route('/gws/{action}/{uri}/', HTTPApp))

        # static dirs
        statics = settings.get_static_dirs()
        for k in statics:
            cls.routes.append(Mount(k, StaticFiles(directory=statics[k]), name=k))

        # home
        cls.routes.append(Route("/", homepage))

        # hello testing route
        cls.routes.append(Route("/hello", hello))

        # user
        #cls.routes.append(Route("/user/", HTTPApp))
        #cls.routes.append(Route("/user/login/", HTTPApp))
        #cls.routes.append(Route("/user/signup/", HTTPApp))

        # adds new routes
        cls.routes.append(Route('/demo/', endpoint=demo_endpoint.demo))
    
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
        # starlette
        cls.app = Starlette(debug=cls.debug, routes=cls.routes, middleware=cls.middleware, on_startup=[cls._on_startup])
        #cls.app = Starlette(debug=cls.debug, routes=cls.routes, on_startup=[cls._on_startup])

        uvicorn.run(cls.app, host=settings.get_data("app_host"), port=settings.get_data("app_port"))
        cls.is_running = True

    @classmethod 
    def _on_startup(cls):
        """
        Called on application startup to create test objects
        """

        from gws.robot import Robot, HTMLRobotViewModel, JSONRobotViewModel

        try:
            robot = Robot.get( Robot.id==1 )
            html_view_model = HTMLRobotViewModel.get( HTMLRobotViewModel.id == 1 )
        except:
            robot = Robot()
            robot.data["name"] = "R. Giskard Reventlov"
            robot.save()
            html_view_model = HTMLRobotViewModel(robot)
            html_view_model.save()
            json_view_model = JSONRobotViewModel(robot)
            json_view_model.save()
        
        host = settings.get_data("app_host")
        if host == "0.0.0.0":
            host = "localhost"

        print("GWS application started!")
        print("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))
        print("* HTTP Testing: http://{}:{}/gws{}".format(host, settings.get_data("app_port"), html_view_model.get_view_url()))    
        #print("* WebSocket Testing: ws://{}:{}/qw{}".format(host, settings.get_data("app_port"), html_view_model.get_view_url()))

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

