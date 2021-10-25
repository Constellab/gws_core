# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import FastAPI
from fastapi.param_functions import Depends
from starlette.exceptions import HTTPException

from gws_core.core.service.settings_service import SettingsService

from .core.exception.exception_handler import ExceptionHandler
from .user.auth_service import AuthService
from .user.user_dto import UserData

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
