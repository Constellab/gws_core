# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import FastAPI
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from .core.exception.exception_handler import ExceptionHandler

core_app = FastAPI(docs_url="/docs")


# Catch HTTP Exceptions
@core_app.exception_handler(HTTPException)
async def allg_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


# Catch all other exceptions
@core_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


@core_app.get("/health-check", summary="Health check route")
async def health_check() -> bool:
    """
    Simple health check route
    """

    return True


class ProcessData(BaseModel):
    uri: str
    type: str = "gws_core.process.process_model.Process"
    title: str = None
    instance_name: str
    config_specs: dict = {}
    input_specs: dict = {}
    output_specs: dict = {}


class ConfigData(BaseModel):
    uri: str = None
    type: str = "gws_core.config.config.Config"
    params: dict = {}


class ProtocolData(ProcessData):
    type: str = "gws_core.protocol.protocol.Protocol"
    interfaces: dict = {}
    outerfaces: dict = {}
