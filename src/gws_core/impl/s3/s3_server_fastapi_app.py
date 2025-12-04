from fastapi import FastAPI
from starlette.exceptions import HTTPException

from gws_core.impl.s3.s3_server_exception_handler import S3ServerExceptionHandler

s3_server_app = FastAPI()


# Catch HTTP Exceptions
@s3_server_app.exception_handler(HTTPException)
async def all_http_exception_handler(request, exc):
    return S3ServerExceptionHandler.handle_exception(request, exc)


# Catch all other exceptions
@s3_server_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return S3ServerExceptionHandler.handle_exception(request, exc)
