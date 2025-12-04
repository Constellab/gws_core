from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from .core.exception.exception_handler import ExceptionHandler

core_app = FastAPI(docs_url="/docs")


# Catch HTTP Exceptions
@core_app.exception_handler(HTTPException)
async def all_http_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


# Catch RequestValidationError (422 Unprocessable Entity)
@core_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return ExceptionHandler.handle_request_validation_error(exc)


# Catch all other exceptions
@core_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


@core_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True
