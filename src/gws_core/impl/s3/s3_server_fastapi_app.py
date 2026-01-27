from starlette.exceptions import HTTPException

from gws_core.core.utils.settings import Settings
from gws_core.impl.s3.s3_server_exception_handler import S3ServerExceptionHandler
from gws_core.lab.api_registry import ApiRegistry

s3_server_app = ApiRegistry.register_api(
    f"/{Settings.s3_server_api_route_path()}/",
    with_exception_handlers=False,
)


# S3 uses its own exception handler (XML responses), not the standard one
@s3_server_app.exception_handler(HTTPException)
async def all_http_exception_handler(request, exc):
    return S3ServerExceptionHandler.handle_exception(request, exc)


# Catch all other exceptions
@s3_server_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return S3ServerExceptionHandler.handle_exception(request, exc)
