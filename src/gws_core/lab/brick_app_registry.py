from fastapi import FastAPI

from gws_core.core.utils.logger import Logger


class BrickAppRegistry:
    """
    Registry that allows external bricks to register custom FastAPI sub-apps.
    Each registered app will be mounted at /brick/{brick_name}/ on the main app.

    Usage from an external brick:

        from fastapi import FastAPI
        from gws_core import BrickAppRegistry

        my_app = FastAPI(docs_url="/docs")

        @my_app.get("/my-route")
        def my_route():
            return {"hello": "world"}

        BrickAppRegistry.register_brick_app("my_brick", my_app)
    """

    # dict of brick_name -> FastAPI app
    _brick_apps: dict[str, FastAPI] = {}

    @classmethod
    def register_brick_app(cls, brick_name: str, app: FastAPI) -> None:
        """Register a custom FastAPI app for a brick.

        The app will be mounted at /brick/{brick_name}/ on the main server.

        :param brick_name: The name of the brick (used as route prefix)
        :param app: The FastAPI sub-app instance
        """
        if brick_name in cls._brick_apps:
            Logger.warning(
                f"Brick app for '{brick_name}' is already registered. Overwriting."
            )
        cls._brick_apps[brick_name] = app
        Logger.info(f"Registered custom FastAPI app for brick '{brick_name}'")

    @classmethod
    def get_all_brick_apps(cls) -> dict[str, FastAPI]:
        """Return all registered brick apps.

        :return: Dict mapping brick_name to FastAPI app
        :rtype: dict[str, FastAPI]
        """
        return cls._brick_apps

    @classmethod
    def clear(cls) -> None:
        """Clear all registered brick apps. Useful for tests."""
        cls._brick_apps = {}
