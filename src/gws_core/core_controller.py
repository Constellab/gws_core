from gws_core.core.utils.settings import Settings
from gws_core.lab.api_registry import ApiRegistry

core_app = ApiRegistry.register_api(
    f"/{Settings.core_api_route_path()}/",
    docs_url="/docs",
    with_exception_handlers=True,
)


@core_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True
