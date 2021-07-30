# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette_context.middleware import ContextMiddleware

from .core.exception import ExceptionHandler

core_app = FastAPI(docs_url="/docs")

# Enable core for the API
core_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

core_app.add_middleware(
    ContextMiddleware
)

# Catch all HTTP exceptions


@core_app.exception_handler(HTTPException)
async def allg_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(exc)


# Catch all other exceptions
@core_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(exc)


@core_app.get("/health-check", summary="Health check route")
async def get_the_experiment_queue() -> dict:
    """
    Simple health check route
    """

    return True


class ProcessData(BaseModel):
    uri: str
    type: str = "gws.process.Process"
    title: str = None
    instance_name: str
    config_specs: dict = {}
    input_specs: dict = {}
    output_specs: dict = {}


class ConfigData(BaseModel):
    uri: str = None
    type: str = "gws.config.Config"
    params: dict = {}


class ProtocolData(ProcessData):
    type: str = "gws.protocol.Protocol"
    interfaces: dict = {}
    outerfaces: dict = {}
