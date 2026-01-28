from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from gws_core.core.exception.exception_handler import ExceptionHandler
from gws_core.core.utils.logger import Logger


class ApiRegistry:
    """
    Registry that creates and stores FastAPI sub-apps.
    Each registered app will be mounted on the main app at the specified path.

    Registration methods:

    - ``register_api(path, ...)`` -- creates a FastAPI app at the given
      mount path. Pass ``with_exception_handlers=True`` to add the standard
      exception handlers automatically.

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

    @classmethod
    def register_api(
        cls,
        path: str,
        docs_url: str | None = None,
        with_exception_handlers: bool = True,
    ) -> FastAPI:
        """Create and register a FastAPI sub-app at the given mount path.

        :param path: The mount path (e.g. "/core-api/" or "/s3-server/")
        :param docs_url: The docs_url passed to FastAPI (None to disable docs)
        :param with_exception_handlers: If True, add the standard exception
            handlers (HTTPException, RequestValidationError, generic Exception)
        :return: The newly created FastAPI app
        """
        if path in cls._apis:
            Logger.warning(f"App at path '{path}' is already registered. Overwriting.")
        app = FastAPI(docs_url=docs_url)
        cls._apis[path] = app
        if with_exception_handlers:
            cls.configure_exception_handlers(app)
        Logger.info(f"Registered FastAPI app at path '{path}'")
        return app

    @classmethod
    def register_brick_api(
        cls,
        brick_name: str,
        docs_url: str | None = "/docs",
        with_exception_handlers: bool = True,
    ) -> FastAPI:
        """Create and register a FastAPI sub-app for an external brick.

        The app is mounted at ``/brick/{brick_name}/`` and has the standard
        exception handlers automatically configured by default.

        :param brick_name: The brick name (used as route prefix)
        :param docs_url: The docs_url passed to FastAPI (default "/docs")
        :param with_exception_handlers: If True (default), add the standard
            exception handlers
        :return: The newly created FastAPI app
        """
        path = cls.get_brick_api_path(brick_name)
        return cls.register_api(
            path, docs_url=docs_url, with_exception_handlers=with_exception_handlers
        )

    @classmethod
    def get_brick_api_path(cls, brick_name: str) -> str:
        """Get the mount path for a registered brick API.

        :param brick_name: The brick name
        :return: The mount path (e.g. "/brick/gws_eln/")
        """
        return f"/brick/{brick_name}/"

    @classmethod
    def configure_exception_handlers(cls, app: FastAPI) -> None:
        """Add standard exception handlers to a FastAPI app.

        Adds handlers for HTTPException, RequestValidationError, and
        generic Exception using the standard ExceptionHandler.

        :param app: The FastAPI app to configure
        """

        def _validation_handler(_request: Request, exc: Exception) -> Response:
            return ExceptionHandler.handle_request_validation_error(exc)  # type: ignore[arg-type]

        app.add_exception_handler(HTTPException, ExceptionHandler.handle_exception)
        app.add_exception_handler(RequestValidationError, _validation_handler)
        app.add_exception_handler(Exception, ExceptionHandler.handle_exception)

    @classmethod
    def get_all_apis(cls) -> dict[str, FastAPI]:
        """Return all registered apis.

        :return: Dict mapping mount_path to FastAPI app
        :rtype: dict[str, FastAPI]
        """
        return cls._apis

    @classmethod
    def clear(cls) -> None:
        """Clear all registered apis. Useful for tests."""
        cls._apis = {}
