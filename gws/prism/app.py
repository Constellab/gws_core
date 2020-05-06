from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse,  PlainTextResponse,  FileResponse,  HTMLResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
import uvicorn

from gws import settings
from gws.prism.view import HTMLView, JSONView
from gws.prism.model import Model
from gws.prism.controller import Controller

async def hello(request):
    return PlainTextResponse("Hello!")

class App :
    """
        GWS application. 
    """

    app: Starlette = None
    ctrl: Controller = None
    routes = [
        Route('/hello', hello),
        Mount('/static', StaticFiles(directory=settings.static_path), name='static'),
    ]
    debug = settings.is_test
    
    @classmethod
    def init(cls):
        cls.app = Starlette(debug=cls.debug, routes=cls.routes, on_startup=[cls.on_startup])
        cls.ctrl = Controller()
        cls.routes.append( Route('/action/{uri}/{params}', cls.action) )


    @classmethod 
    def start(cls):
        uvicorn.run(cls.app, host=settings.app_host, port=settings.app_port)

    @classmethod 
    def on_startup(cls):
        pass
    
    @classmethod
    async def action(cls, request) -> str:
        """
        Return a response
        """
        return await cls.ctrl.action(request)

    @classmethod 
    def test(cls, url):
        """
        Return a response in test mode
        """
        from starlette.testclient import TestClient
        client = TestClient(cls.app)
        response = client.get(url)
        return response

# initialize the app
App.init()

# put in user app.py file
# app = gws.prism.App()
# if __name__ == "__main__":
#     uvicorn.run(app.app, host='0.0.0.0', port=8000)