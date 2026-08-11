"""The two public routes over which the lab hands out its Claude Code plugin.

============================================  ===================  ==================
Route                                          Stability            Who reads it
============================================  ===================  ==================
``GET /plugins/marketplace.json``              **never changes**    the user, once
``GET /plugins/<plugin>-<version>.zip``        changes per version  nobody by hand
============================================  ===================  ==================

The user runs ``/plugin marketplace add https://<lab api url>/plugins/marketplace.json``
once and never returns to that URL. The archive's URL lives inside the manifest and
carries the version, so it moves freely -- which is what keeps a proxy from answering a
new version's URL with the zip it cached for the previous one.

Both routes are unauthenticated, because a Claude Code client has no lab credentials
until it has installed the plugin and gone through the MCP login. What they serve is
public by construction (see :mod:`gws_core.mcp.plugin_generator`).

Registered from ``mount_mcp_app``'s caller, in the same conditional block as ``/mcp/``:
with the MCP server off, an installed plugin would connect to nothing, and a 404 on the
marketplace is a far more legible failure than a plugin that silently never works.
"""

from starlette.responses import JSONResponse, Response

from gws_core.core.utils.logger import Logger
from gws_core.lab.api_registry import ApiRegistry
from gws_core.mcp.plugin_generator import (
    MARKETPLACE_FILE_NAME,
    PLUGINS_ROUTE_PATH,
    PluginGenerator,
    build_marketplace_url,
)

# The archive URL carries the version, so it may be cached forever. The manifest is the
# one thing that must be re-read to discover a new version.
ARCHIVE_CACHE_CONTROL = "public, max-age=31536000, immutable"
MARKETPLACE_CACHE_CONTROL = "no-cache"


def get_marketplace() -> JSONResponse:
    """Serve the marketplace manifest, generated from this lab's own identity."""
    generated = PluginGenerator.get_generated()

    return JSONResponse(
        generated.marketplace_manifest,
        headers={"Cache-Control": MARKETPLACE_CACHE_CONTROL},
    )


def get_plugin_archive(file_name: str) -> Response:
    """Serve the plugin archive, but only under the name the manifest announces.

    A client that kept a manifest from before an upgrade asks for a version this lab no
    longer has. Answering with the current archive would serve content under a URL
    announcing another version -- exactly what the versioned URL exists to prevent -- so
    the answer is a 404 saying what to do about it.
    """
    generated = PluginGenerator.get_generated()

    if file_name != generated.archive_file_name:
        return JSONResponse(
            {
                "detail": (
                    f"This lab does not serve '{file_name}'. It now serves version "
                    f"{generated.version}. Run '/plugin marketplace update "
                    f"{generated.identity.marketplace_name}' to refresh it, then install again."
                )
            },
            status_code=404,
        )

    return Response(
        content=generated.archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{generated.archive_file_name}"',
            "Cache-Control": ARCHIVE_CACHE_CONTROL,
        },
    )


def register_plugin_routes() -> None:
    """Register the plugin distribution routes as a lab sub-app.

    Called only when the MCP server is enabled, so with MCP off neither route exists.
    """
    plugins_app = ApiRegistry.register_api(f"/{PLUGINS_ROUTE_PATH}/")

    # The manifest first: its path would otherwise be swallowed by the archive route.
    plugins_app.get(f"/{MARKETPLACE_FILE_NAME}")(get_marketplace)
    plugins_app.get("/{file_name}")(get_plugin_archive)

    Logger.info(f"Claude Code marketplace available at {build_marketplace_url()}")
