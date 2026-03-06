from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from gws_core.core.utils.request_context import RequestContext


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request_id to each HTTP request.

    The request_id is stored in a ContextVar so it is automatically available
    in all logs produced during the request lifecycle. It is also returned
    in the X-Request-ID response header for end-to-end tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = RequestContext.generate_and_set_request_id()

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
