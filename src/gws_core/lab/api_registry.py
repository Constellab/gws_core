import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from gws_core.core.classes.cors_config import CorsPolicy, LabDefaultCorsMiddleware
from gws_core.core.classes.security_headers import SecurityHeadersMiddleware
from gws_core.core.exception.exception_handler import ExceptionHandler
from gws_core.core.utils.logger import Logger


class _SilentAccessLogFilter(logging.Filter):
    """Filter that suppresses access log entries for specific paths.

    This prevents high-volume routes (e.g. S3 server called by rclone)
    from flooding the logs.
    """

    def __init__(self, silent_paths: list[str]) -> None:
        super().__init__()
        self._silent_paths = silent_paths

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return all(silent_path not in message for silent_path in self._silent_paths)


class ApiRegistry:
    """
    Registry that creates and stores FastAPI sub-apps.
    Each registered app will be mounted on the main app at the specified path.

    Registration methods:

    - ``register_api(path, ...)`` -- creates a FastAPI app at the given
      mount path. Pass ``with_exception_handlers=True`` to add the standard
      exception handlers automatically. Pass ``silent_access_log=True`` to
      downgrade access logs for this path to DEBUG level.

    - ``register_brick_app(brick_name, ...)`` -- convenience wrapper that
      calls ``register_api`` with path ``/brick/{brick_name}/`` and
      ``with_exception_handlers=True`` by default.

    - ``configure_exception_handlers(app)`` -- public helper that adds the
      three standard exception handlers (HTTPException, RequestValidationError,
      generic Exception) to any FastAPI app.

    Usage from an external brick::

        from gws_core import ApiRegistry

        eln_app = ApiRegistry.register_brick_api("gws_eln")

        @eln_app.get("/my-route")
        def my_route():
            return {"hello": "world"}
    """

    # dict of mount_path -> FastAPI app
    _apis: dict[str, FastAPI] = {}

    # paths whose access logs are downgraded to DEBUG
    _silent_paths: list[str] = []

    @classmethod
    def register_api(
        cls,
        path: str,
        docs_url: str | None = None,
        with_exception_handlers: bool = True,
        with_security_headers: bool = True,
        silent_access_log: bool = False,
        cors: CorsPolicy | None = None,
    ) -> FastAPI:
        """Create and register a FastAPI sub-app at the given mount path.

        :param path: The mount path (e.g. "/core-api/" or "/s3-server/")
        :param docs_url: The docs_url passed to FastAPI (None to disable docs)
        :param with_exception_handlers: If True, add the standard exception
            handlers (HTTPException, RequestValidationError, generic Exception)
        :param with_security_headers: If True (default), add the standard security
            headers (CSP, HSTS, ...) to every response of this app. Disable only
            for machine-to-machine APIs that no browser ever calls.
        :param silent_access_log: If True, downgrade access logs for this path
            to DEBUG level (visible only with --log-level=DEBUG)
        :param cors: A :class:`CorsPolicy` this app applies to **all** of its
            routes, replacing the lab default (lab sub-domains only, with
            credentials) for this app. Declare the policy here rather than adding
            a CORS middleware on the returned app yourself, so it replaces the
            lab default instead of stacking on top of it.
        :return: The newly created FastAPI app
        """
        if path in cls._apis:
            Logger.warning(f"App at path '{path}' is already registered. Overwriting.")
        app = FastAPI(docs_url=docs_url)
        cls._apis[path] = app
        if with_exception_handlers:
            cls.configure_exception_handlers(
                app, cors_policy=cors, with_security_headers=with_security_headers
            )
        if silent_access_log:
            cls._silent_paths.append(path)
        # The app owns its CORS: its declared policy, or the lab default. This only
        # works because the MAIN app has no CORS middleware — one on the parent
        # would answer preflights before the mount is reached, overriding this
        # app's policy. The default is a lazily-resolved subclass because it reads
        # Settings, which may not be loaded yet at brick import time.
        if cors is not None:
            app.add_middleware(CORSMiddleware, **cors.middleware_kwargs())
        else:
            app.add_middleware(LabDefaultCorsMiddleware)
        if with_security_headers:
            # Added after — thus outside — the CORS middleware, so preflight
            # responses carry the security headers too.
            app.add_middleware(SecurityHeadersMiddleware)
        Logger.debug(f"Registered FastAPI app at path '{path}'")
        return app

    @classmethod
    def register_brick_api(
        cls,
        brick_name: str,
        docs_url: str | None = "/docs",
        with_exception_handlers: bool = True,
        with_security_headers: bool = True,
        cors: CorsPolicy | None = None,
    ) -> FastAPI:
        """Create and register a FastAPI sub-app for an external brick.

        The app is mounted at ``/brick/{brick_name}/`` and has the standard
        exception handlers automatically configured by default.

        :param brick_name: The brick name (used as route prefix)
        :param docs_url: The docs_url passed to FastAPI (default "/docs")
        :param with_exception_handlers: If True (default), add the standard
            exception handlers
        :param with_security_headers: If True (default), add the standard security
            headers to every response (see ``register_api``)
        :param cors: A :class:`CorsPolicy` overriding the lab-wide CORS for every
            route of this brick's app (see ``register_api``)
        :return: The newly created FastAPI app
        """
        path = cls.get_brick_api_path(brick_name)
        return cls.register_api(
            path,
            docs_url=docs_url,
            with_exception_handlers=with_exception_handlers,
            with_security_headers=with_security_headers,
            cors=cors,
        )

    @classmethod
    def get_brick_api_path(cls, brick_name: str) -> str:
        """Get the mount path for a registered brick API.

        :param brick_name: The brick name
        :return: The mount path (e.g. "/brick/gws_eln/")
        """
        return f"/brick/{brick_name}/"

    @classmethod
    def configure_exception_handlers(
        cls,
        app: FastAPI,
        cors_policy: CorsPolicy | None = None,
        with_security_headers: bool = True,
    ) -> None:
        """Add standard exception handlers to a FastAPI app.

        Adds handlers for HTTPException, RequestValidationError, and
        generic Exception using the standard ExceptionHandler.

        The generic Exception handler's responses never traverse the app's
        middleware (they are produced above it, by ServerErrorMiddleware), so the
        headers the app's middleware would have set are stamped manually — hence
        the two parameters below, which must mirror the app's middleware setup.

        :param app: The FastAPI app to configure
        :param cors_policy: The app's CORS policy override (None for the lab
            default), applied to the generic handler's 500 responses
        :param with_security_headers: whether the app has the standard security
            headers, to apply them to the generic handler's responses too
        """

        def _validation_handler(_request: Request, exc: Exception) -> Response:
            return ExceptionHandler.handle_request_validation_error(exc)  # type: ignore[arg-type]

        def _generic_handler(request: Request, exc: Exception) -> Response:
            response = ExceptionHandler.handle_exception(request, exc, cors_policy=cors_policy)
            if with_security_headers:
                SecurityHeadersMiddleware.add_security_headers(response)
            return response

        app.add_exception_handler(HTTPException, ExceptionHandler.handle_exception)
        app.add_exception_handler(RequestValidationError, _validation_handler)
        app.add_exception_handler(Exception, _generic_handler)

    @classmethod
    def get_all_apis(cls) -> dict[str, FastAPI]:
        """Return all registered apis.

        :return: Dict mapping mount_path to FastAPI app
        :rtype: dict[str, FastAPI]
        """
        return cls._apis

    @classmethod
    def install_access_log_filter(cls) -> None:
        """Install the access log filter on uvicorn's access logger.

        Downgrades log entries to DEBUG for all paths registered with
        ``silent_access_log=True``. Call this before ``uvicorn.run()``.
        """
        if cls._silent_paths:
            access_logger = logging.getLogger("uvicorn.access")
            access_logger.addFilter(_SilentAccessLogFilter(cls._silent_paths))

    @classmethod
    def clear(cls) -> None:
        """Clear all registered apis. Useful for tests."""
        cls._apis = {}
        cls._silent_paths = []
