"""The public routes over which the lab hands out its Claude Code plugin.

============================================  ===================  ==================
Route                                          Stability            Who reads it
============================================  ===================  ==================
``GET /plugins/marketplace.json``              **never changes**    the user, once
``GET /plugins/<plugin>-<version>.zip``        changes per version  nobody by hand
``GET /plugins/install-dev.sh``                **never changes**    a developer, piped
``GET /plugins/install-dev.ps1``               **never changes**    a developer, piped
============================================  ===================  ==================

The user runs ``/plugin marketplace add https://<lab api url>/plugins/marketplace.json``
once and never returns to that URL. The archive's URL lives inside the manifest and
carries the version, so it moves freely -- which is what keeps a proxy from answering a
new version's URL with the zip it cached for the previous one.

The two ``install-dev`` scripts serve the case the marketplace channel cannot: a lab on
``http://localhost``, whose plugin Claude Code refuses to fetch itself (see
:mod:`gws_core.mcp.plugin_dev_install`). They are served unconditionally rather than only
by a lab that needs them -- a pinned local copy is a legitimate way to debug any lab, and a
route that exists only sometimes is one nobody can document.

Both routes are unauthenticated, because a Claude Code client has no lab credentials
until it has installed the plugin and gone through the MCP login. What they serve is
public by construction (see :mod:`gws_core.mcp.plugin_generator`).

Registered from ``mount_mcp_app``'s caller, in the same conditional block as ``/mcp/``:
with the MCP server off, an installed plugin would connect to nothing, and a 404 on the
marketplace is a far more legible failure than a plugin that silently never works.

Beside them, on the lab's ordinary authenticated API, one route describes the plugin to
the lab's **own** front-end (``GET /core-api/claude-plugin``). That one always exists:
telling a user why their lab serves no plugin is exactly what the screen is for.
"""

from fastapi.param_functions import Depends
from starlette.responses import JSONResponse, Response

from gws_core.core.exception.exceptions.not_found_exception import NotFoundException
from gws_core.core.utils.logger import Logger
from gws_core.core_controller import core_app
from gws_core.lab.api_registry import ApiRegistry
from gws_core.mcp.plugin_dev_install import (
    POSIX_SCRIPT_FILE_NAME,
    WINDOWS_SCRIPT_FILE_NAME,
    build_posix_script,
    build_windows_script,
)
from gws_core.mcp.plugin_dto import ClaudePluginInfoDTO
from gws_core.mcp.plugin_generator import (
    MARKETPLACE_FILE_NAME,
    PLUGINS_ROUTE_PATH,
    PluginGenerator,
    build_marketplace_url,
)
from gws_core.mcp.plugin_service import PluginService
from gws_core.user.authorization_service import AuthorizationService

# The archive URL carries the version, so it may be cached forever. The manifest is the
# one thing that must be re-read to discover a new version.
ARCHIVE_CACHE_CONTROL = "public, max-age=31536000, immutable"
MARKETPLACE_CACHE_CONTROL = "no-cache"

# The install scripts name the current version, and re-downloading one is how a developer
# picks up a new one. A cached copy would send them at an archive the lab no longer serves.
SCRIPT_CACHE_CONTROL = "no-cache"


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

    :raises NotFoundException: When the name is not the one the manifest announces.
    """
    generated = PluginGenerator.get_generated()

    if file_name != generated.archive_file_name:
        raise NotFoundException(
            f"This lab does not serve '{file_name}'. It now serves version "
            f"{generated.version}. Run '/plugin marketplace update "
            f"{generated.identity.marketplace_name}' to refresh it, then install again."
        )

    return Response(
        content=generated.archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{generated.archive_file_name}"',
            "Cache-Control": ARCHIVE_CACHE_CONTROL,
        },
    )


def get_dev_install_script_posix() -> Response:
    """Serve the bash install script, for macOS and Linux."""
    return _script_response(build_posix_script())


def get_dev_install_script_windows() -> Response:
    """Serve the PowerShell install script, for Windows."""
    return _script_response(build_windows_script())


def _script_response(script: str) -> Response:
    """A script, served as text.

    ``text/plain`` for both: a shell reads what is piped into it whatever the type says,
    while a browser -- where a developer checks what they are about to run -- displays plain
    text and downloads anything else.
    """
    return Response(
        content=script,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": SCRIPT_CACHE_CONTROL},
    )


@core_app.get(
    "/claude-plugin",
    tags=["Claude plugin"],
    summary="Describe the Claude Code plugin this lab serves",
)
def get_claude_plugin_info(
    _=Depends(AuthorizationService.check_user_access_token),
) -> ClaudePluginInfoDTO:
    """What this lab's Claude Code screen shows: the commands to run, or why there are none.

    Authenticated like the rest of the lab API: it is read by the lab's front-end, for a
    user who is already signed in. The manifest itself stays public -- a Claude Code
    client has no lab credentials until it has installed the plugin.
    """
    return PluginService.get_plugin_info()


def register_plugin_routes() -> None:
    """Register the plugin distribution routes as a lab sub-app.

    Called only when the MCP server is enabled, so with MCP off neither route exists.
    """
    plugins_app = ApiRegistry.register_api(f"/{PLUGINS_ROUTE_PATH}/")

    # Every named path first: they would otherwise be swallowed by the archive route, which
    # matches any single segment and answers a 404 naming the version it does serve.
    plugins_app.get(f"/{MARKETPLACE_FILE_NAME}")(get_marketplace)
    plugins_app.get(f"/{POSIX_SCRIPT_FILE_NAME}")(get_dev_install_script_posix)
    plugins_app.get(f"/{WINDOWS_SCRIPT_FILE_NAME}")(get_dev_install_script_windows)
    plugins_app.get("/{file_name}")(get_plugin_archive)

    Logger.info(f"Claude Code marketplace available at {build_marketplace_url()}")
