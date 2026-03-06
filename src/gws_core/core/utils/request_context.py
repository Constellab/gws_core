import uuid
from contextvars import ContextVar

# Request-scoped context variable for correlating all logs from a single HTTP request
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestContext:
    """Provides access to the current request context.

    Uses contextvars to store a unique request_id per HTTP request.
    This allows correlating all log entries produced during the same request.
    """

    @classmethod
    def get_request_id(cls) -> str | None:
        """Get the current request_id, or None if not in a request context."""
        return _request_id_ctx.get()

    @classmethod
    def set_request_id(cls, request_id: str) -> None:
        """Set the request_id for the current context."""
        _request_id_ctx.set(request_id)

    @classmethod
    def generate_and_set_request_id(cls) -> str:
        """Generate a new UUID request_id and set it in the current context."""
        request_id = str(uuid.uuid4())
        cls.set_request_id(request_id)
        return request_id

    @classmethod
    def clear(cls) -> None:
        """Clear the request_id from the current context."""
        _request_id_ctx.set(None)
