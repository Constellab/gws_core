

from threading import Thread

import uvicorn
from fastapi import FastAPI
from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_controller import external_lab_app
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app
from gws_core.lab.system_event import SystemStartedEvent
from gws_core.model.event.event_dispatcher import EventDispatcher
from starlette_context.middleware.context_middleware import ContextMiddleware

from .core.classes.cors_config import CorsConfig
from .core.classes.security_headers import SecurityHeadersMiddleware
from .core_controller import core_app
from .lab.system_service import SystemService
from .space.space_controller import space_app

app = FastAPI(docs_url=None)

####################################################################################
#
# Startup & Shutdown Events
#
####################################################################################


@app.on_event("startup")
def startup():
    """ Called before the app is started """

    App.init()


@app.on_event("shutdown")
def shutdown():
    """ Called before the application is stopped """

    App.deinit()

####################################################################################
#
# App class
#
####################################################################################


class App:
    """
    Base App
    """

    app: FastAPI = app
    is_running: bool = False

    @classmethod
    def init(cls):
        """
        Initialize the app
        """

        cls.is_running = True
        SystemService.init_queue_and_monitor()

    @classmethod
    def deinit(cls):
        """
        Deinitialize the app
        """

        SystemService.deinit_queue_and_monitor()
        cls.is_running = False

    @classmethod
    def start(cls, port: int = 3000):
        """
        Starts FastAPI uvicorn
        """

        SystemService.init()

        # Configure the CORS
        CorsConfig.configure_app_cors(app)

        # Add security headers middleware
        app.add_middleware(SecurityHeadersMiddleware)

        # Registrer the lab start. Use a new thread to prevent blocking the start
        th = Thread(target=SystemService.register_lab_start)
        th.start()

        # Dispatch the system started event
        EventDispatcher.get_instance().dispatch(SystemStartedEvent())

        cls.start_uvicorn_app(port)

    @classmethod
    def start_uvicorn_app(cls, port: int = 3000):
        # configure the context middleware
        cls.app.add_middleware(
            ContextMiddleware
        )

        # api routes
        cls.app.mount(f"/{Settings.core_api_route_path()}/", core_app)
        cls.app.mount(f"/{Settings.space_api_route_path()}/", space_app)
        cls.app.mount(f"/{Settings.external_lab_api_route_path()}/", external_lab_app)
        cls.app.mount(f"/{Settings.s3_server_api_route_path()}/", s3_server_app)

        uvicorn.run(cls.app, host='0.0.0.0', port=int(port))
