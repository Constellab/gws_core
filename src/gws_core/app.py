from contextlib import asynccontextmanager
from threading import Thread

import uvicorn
from fastapi import FastAPI
from starlette_context.middleware.context_middleware import ContextMiddleware

from gws_core.core.utils.logger import Logger
from gws_core.lab.system_event import SystemStartedEvent, SystemStoppedEvent
from gws_core.mcp.mcp_controller import mcp_session_manager_lifespan, mount_mcp_app
from gws_core.mcp.plugin_controller import register_plugin_routes
from gws_core.model.event.event_dispatcher import EventDispatcher

from .apps.apps_manager import AppsManager
from .core.classes.request_id_middleware import RequestIdMiddleware
from .core.utils.settings import Settings
from .lab.api_registry import ApiRegistry
from .lab.system_service import SystemService

####################################################################################
#
# Lifespan Events
#
####################################################################################


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events
    """
    # Startup: code before yield
    # The MCP server keeps its sessions in a task group started by its own
    # lifespan. Starlette does not run the lifespan of a *mounted* sub-app, so
    # without this the manager stays uninitialized and every authenticated MCP
    # call fails with "Task group is not initialized".
    async with mcp_session_manager_lifespan():
        yield
    # Shutdown: code after yield
    App.deinit()


app = FastAPI(docs_url=None, lifespan=lifespan)


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

    @classmethod
    def deinit(cls):
        """
        Deinitialize the app
        """
        AppsManager.stop_all_processes()
        SystemService.deinit_queue_and_monitor()
        # Dispatch the system stopped event
        EventDispatcher.get_instance().dispatch(SystemStoppedEvent())

    @classmethod
    def start(cls, port: int = 3000):
        """
        Starts FastAPI uvicorn
        """

        SystemService.init()

        SystemService.init_queue_and_monitor()

        # No CORS or security-headers middleware on the main app: each sub-app gets
        # its own from ApiRegistry.register_api — CORS because a parent CORS
        # middleware would answer preflights before the mounts are reached,
        # overriding the sub-apps' policies; security headers so an app can opt
        # out (with_security_headers=False).

        # Add request ID middleware (outermost — runs first, sets request_id for all logs)
        app.add_middleware(RequestIdMiddleware)

        # Registrer the lab start. Use a new thread to prevent blocking the start
        th = Thread(target=SystemService.register_lab_start)
        th.start()

        # Dispatch the system started event
        EventDispatcher.get_instance().dispatch(SystemStartedEvent())

        cls.start_uvicorn_app(port)

    @classmethod
    def start_uvicorn_app(cls, port: int = 3000):
        # configure the context middleware
        cls.app.add_middleware(ContextMiddleware)

        # Build and register the MCP server. Done here (not at import) because its
        # OAuth issuer/resource URLs are read from Settings, and before the loop
        # below so its sub-apps are part of the mount. Gated OFF by default: when
        # the env var is not set, neither /mcp/ nor the OAuth provider is created.
        if Settings.is_mcp_server_enabled():
            mount_mcp_app(cls.app)
            # The plugin the lab hands out is a connection to that endpoint plus the
            # skills that drive it, so it is registered in the same block: with MCP off,
            # an installed plugin would connect to nothing.
            register_plugin_routes()
            Logger.info("MCP server enabled; mounting /mcp/ and the OAuth provider.")
        else:
            Logger.debug(
                f"MCP server disabled ({Settings.MCP_SERVER_ENABLED_ENV_VAR} != 'true'); "
                "not mounting /mcp/, /plugins/ or the OAuth provider."
            )

        # Mount all registered apps (internal + brick apps)
        for path, sub_app in ApiRegistry.get_all_apis().items():
            cls.app.mount(path, sub_app)

        # Install access log filter for silent APIs (e.g. S3 server)
        ApiRegistry.install_access_log_filter()

        # Mark this process as the HTTP server so fork-based scenario execution
        # (ScenarioProxy.run()) can refuse to run inside a request handler.
        Settings.get_instance().set_is_http_server(True)

        uvicorn.run(cls.app, host="0.0.0.0", port=int(port))
