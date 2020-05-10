from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse, PlainTextResponse,  FileResponse,  HTMLResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.endpoints import HTTPEndpoint, WebSocketEndpoint
from peewee import ForeignKeyField

import uvicorn

from gws.settings import Settings
from gws.prism.view import HTMLViewTemplate, JSONViewTemplate, PlainTextViewTemplate
from gws.prism.model import Resource, ViewModel
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
# Robot classÒ
#
####################################################################################

class Robot(Resource):
    pass

class RobotHTMLViewModel(ViewModel):
    name = 'gws.test.robot-html-view'
    template = HTMLViewTemplate("""
        Hi!<br>
        I'am {{view_model.model.data.name}}.<br>
        Welcome to GWS!
    """)
    model: Robot = ForeignKeyField(Robot, backref='view_model')

class RobotJSONViewModel(ViewModel):
    name = 'gws.test.robot-json-view'
    template = JSONViewTemplate('{"name":"{{view_model.data.name}}"}')
    model: Robot = ForeignKeyField(Robot, backref='view_model')
    
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
# Endpoints
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
        Mount('/static', StaticFiles(directory=settings.get_data("static_path")), name='static'),
    ]
    debug = settings.get_data("is_test")
    is_started = False

    @classmethod
    def init(cls):
        cls.routes.append(WebSocketRoute('/ws/{action}/{uri_name}/{uri_id}/{params}/', WebSocketApp))
        cls.routes.append(WebSocketRoute('/ws/{action}/{uri_name}/{uri_id}/', WebSocketApp))
        cls.routes.append(Route('/{action}/{uri_name}/{uri_id}/{params}/', HTTPApp) )
        cls.routes.append(Route('/{action}/{uri_name}/{uri_id}/', HTTPApp) )
        cls.app = Starlette(debug=cls.debug, routes=cls.routes, on_startup=[cls.on_startup])
    
    @classmethod
    async def action(cls, request) -> Response:
        """
        Return a response
        """

        view_model = await Controller.action(request)
        if isinstance(view_model.template, HTMLViewTemplate):
            return HTMLResponse(view_model.render())
        elif isinstance(view_model.template, JSONViewTemplate):
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
            view_model = RobotHTMLViewModel.get( RobotHTMLViewModel.id == 1 )
        except:
            robot = Robot()
            robot.insert_data({"name":"R. Giskard Reventlov"})
            robot.save()
            view_model = RobotHTMLViewModel(robot)
            view_model.save()

        print("GWS application started!")
        print("Server: {}:{}".format(settings.get_data("app_host"), settings.get_data("app_port")))
        print("Testing the app: http://{}:{}{}".format(settings.get_data("app_host"), settings.get_data("app_port"), view_model.get_update_view_uri()))
    
    @classmethod
    async def ws_action(cls, websocket):
        await websocket.accept()
        await websocket.send_text('Hello, websocket!')
        await websocket.close()

    
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


# put in user app.py file
# app = gws.prism.App()
# if __name__ == "__main__":
#     uvicorn.run(app.app, host='0.0.0.0', port=8000)