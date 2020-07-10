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
    app = settings.data.get("app", {})
    text_script = """
        window.addEventListener("load", function(event) {
            """ + app.get("onload","") + ";" + """
        });
    """

    print("----------")
    print(settings.app)
    return templates.TemplateResponse('index.html', {'request': request, "settings": settings})

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
    
Robot.register_view_models([
    RobotHTMLViewModel, 
    RobotJSONViewModel
])

Controller.register_models([
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
        GWS application. 
    """

    app: Starlette = None
    ctrl: Controller = None
    routes = [
        Route('/hello', hello),
    ]
    debug = settings.get_data("is_test")
    is_started = False

    @classmethod
    def init(cls):
        # process and resource routes
        cls.routes.append(WebSocketRoute('/qw/{action}/{uri_name}/{uri_id}/{params}/', WebSocketApp))
        cls.routes.append(WebSocketRoute('/qw/{action}/{uri_name}/{uri_id}/', WebSocketApp))
        cls.routes.append(Route('/q/{action}/{uri_name}/{uri_id}/{params}/', HTTPApp) )
        cls.routes.append(Route('/q/{action}/{uri_name}/{uri_id}/', HTTPApp) )

        # static module dirs
        statics = settings.get_static_dirs()
        for k in statics:
            print(statics[k])
            cls.routes.append(Mount(k, StaticFiles(directory=statics[k]), name=k))

        # home
        cls.routes.append(Route("/", homepage))

        # starlette
        cls.app = Starlette(debug=cls.debug, routes=cls.routes, on_startup=[cls.on_startup])
    
    @classmethod
    async def action(cls, request) -> Response:
        """
        Return a response
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
        uvicorn.run(cls.app, host=settings.get_data("app_host"), port=settings.get_data("app_port"))
        App.is_started = True

    @classmethod 
    def on_startup(cls):
        try:
            robot = Robot.get( Robot.id==1 )
            html_view_model = RobotHTMLViewModel.get( RobotHTMLViewModel.id == 1 )
        except:
            robot = Robot()
            robot.insert_data({"name":"R. Giskard Reventlov"})
            robot.save()
            html_view_model = RobotHTMLViewModel(robot)
            html_view_model.save()
            json_view_model = RobotJSONViewModel(robot)
            json_view_model.save()
            
        print("GWS application started!")
        print("* Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))
        print("* HTTP Testing: http://{}:{}/q{}".format(settings.get_data("app_host"), settings.get_data("app_port"), html_view_model.get_view_uri()))    
        print("* WebSocket Testing: ws://{}:{}/qw{}".format(settings.get_data("app_host"), settings.get_data("app_port"), html_view_model.get_view_uri()))

    @classmethod 
    def test(cls, url):
        """
        Return a response in test mode
        """
        from starlette.testclient import TestClient
        client = TestClient(cls.app)
        response = client.get(url)
        return response

####################################################################################
#
# Initialize the app
#
####################################################################################

App.init()
