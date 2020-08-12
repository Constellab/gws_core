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

from gws.settings import Settings
from gws.prism.view import HTMLViewTemplate, JSONViewTemplate, PlainTextViewTemplate
from gws.prism.model import Resource, ResourceViewModel
from gws.prism.controller import Controller

settings = Settings.retrieve()

####################################################################################
#
# Hello!
#
####################################################################################

async def hello(request):
    return PlainTextResponse("Hello!")

####################################################################################
#
# Homepage!
#
####################################################################################

templates = Jinja2Templates(directory=settings.get_public_dir())
async def homepage(request):
    settings = Settings.retrieve()
    return templates.TemplateResponse('index.html', {
        'request': request, 
        'settings': settings,
    })

####################################################################################
#
# Robot class
#
####################################################################################

class Robot(Resource):
    pass

class RobotHTMLViewModel(ResourceViewModel):
    template = HTMLViewTemplate("""
        Hi!<br>
        I'am {{view_model.model.data.name}}.<br>
        Welcome to GWS!
    """)

class RobotJSONViewModel(ResourceViewModel):
    template = JSONViewTemplate('{"name":"{{view_model.model.data.name}}"}')
    
Robot.register_view_model_specs([
    RobotHTMLViewModel, 
    RobotJSONViewModel
])

Controller.register_model_specs([
    Robot,
    RobotHTMLViewModel,
    RobotJSONViewModel
])

####################################################################################
#
# HTTP and WebSocket endpoints
#
####################################################################################

class HTTPApp(HTTPEndpoint):
    async def get(self, request):
        return await App.action(request)
    
    async def post(self, request):
        return await App.action(request)

class WebSocketApp(WebSocketEndpoint):
    encoding = 'bytes'

    async def on_connect(self, websocket):
        await websocket.accept()

    async def on_receive(self, websocket, data):
        view = await App.action(websocket)
        html = view.render()
        await websocket.send_bytes(b""+html)
        #await websocket.send_bytes(b"Message: " + data)

    async def on_disconnect(self, websocket, close_code):
        pass

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
    routes = [
        Route('/hello', hello),
    ]
    debug = settings.get_data("is_test")
    is_running = False

    @classmethod
    def _init(cls):
        """
        Initializes the application. This method is automatically called after by the constructor. 
        It calls on_init() method to perform custom user initializations
        """

        cls.on_init()

        # process and resource routes
        cls.routes.append(Route('/gws/{action}/{uri}/{params}/', HTTPApp))
        cls.routes.append(Route('/gws/{action}/{uri}/', HTTPApp))

        # static dirs
        statics = settings.get_static_dirs()
        for k in statics:
            cls.routes.append(Mount(k, StaticFiles(directory=statics[k]), name=k))

        # home
        cls.routes.append(Route("/", homepage))

        # starlette
        cls.app = Starlette(debug=cls.debug, routes=cls.routes, on_startup=[cls._on_startup])
    
    @classmethod
    async def action(cls, request) -> Response:
        """
        Deals a user action and returns a response
        :return: The response
        :rtype: `starlette.responses.Response`
        """
        view_model = await Controller.action(request)
        if view_model.template.is_html():
            return HTMLResponse(view_model.render())
        elif view_model.template.is_json():
            return JSONResponse(view_model.render())
        else:
            return PlainTextResponse(view_model.render())

    @classmethod 
    def start(cls):
        """
        Starts the starlette uvicorn web application
        """
        cls._init()
        uvicorn.run(cls.app, host=settings.get_data("app_host"), port=settings.get_data("app_port"))
        cls.is_running = True

    @classmethod
    def on_init(cls):
        """
        Initializes the application. This method is automatically called after by the constructor
        """
        pass

    @classmethod 
    def _on_startup(cls):
        """
        Called on application startup to create test objects
        """
        try:
            robot = Robot.get( Robot.id==1 )
            html_view_model = RobotHTMLViewModel.get( RobotHTMLViewModel.id == 1 )
        except:
            robot = Robot()
            robot.data["name"] = "R. Giskard Reventlov"
            robot.save()
            html_view_model = RobotHTMLViewModel(robot)
            html_view_model.save()
            json_view_model = RobotJSONViewModel(robot)
            json_view_model.save()
        
        host = settings.get_data("app_host")
        if host == "0.0.0.0":
            host = "localhost"

        print("GWS application started!")
        print("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))
        print("* HTTP Testing: http://{}:{}/gws{}".format(host, settings.get_data("app_port"), html_view_model.get_view_uri()))    
        #print("* WebSocket Testing: ws://{}:{}/qw{}".format(host, settings.get_data("app_port"), html_view_model.get_view_uri()))

    @classmethod 
    def test(cls, url: str) -> Response:
        """
        Returns a response in test mode
        :param url: The test url
        :type url: str
        :return: The response
        :rtype: `starlette.responses.Response`
        """
        cls._init()
        from starlette.testclient import TestClient
        client = TestClient(cls.app)
        response = client.get(url)
        return response

