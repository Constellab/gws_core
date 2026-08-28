"""Mounts the MCP server into the lab's FastAPI app.

Serving MCP from the lab process (rather than as a standalone service) reuses the
lab's TLS, domain, and -- critically -- its ``secret_key``, so the JWT the OAuth
flow mints is the very token :class:`JWTService` already validates.

``/mcp/`` holds the MCP endpoint itself (Streamable HTTP) plus, courtesy of the SDK,
the OAuth discovery documents, ``/register``, ``/authorize`` and ``/token``.

Only the MCP-specific parts live here. The authorization server itself, and the
browser-facing consent route that completes a login, belong to any OAuth client and
live in :mod:`gws_core.oauth`.

Security headers are disabled on ``/mcp/``: it is a machine-to-machine API that no
browser renders (see ``ApiRegistry.register_api``).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI
from mcp.server.auth.handlers.metadata import MetadataHandler
from mcp.server.auth.routes import (
    build_metadata,
    cors_middleware,
    create_protected_resource_routes,
)
from mcp.server.auth.settings import (
    AuthSettings,
    ClientRegistrationOptions,
    RevocationOptions,
)
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl
from starlette.routing import Route

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.lab.api_registry import ApiRegistry
from gws_core.mcp.mcp_server_builder import build_mcp_server
from gws_core.oauth.oauth_provider import LabOAuthProvider
from gws_core.oauth.oauth_service import OAuthService

MCP_ROUTE_PATH = "mcp"

# How this resource is named to a user on the consent page.
MCP_RESOURCE_NAME = "MCP server"


def get_lab_base_url() -> str:
    """Return the lab's externally reachable base URL (no trailing slash)."""
    return Settings.get_lab_api_url().rstrip("/")


def get_mcp_url() -> str:
    """The canonical MCP resource URL; also the OAuth issuer.

    Public because the generated plugin points its MCP server at this exact URL: the
    address a client is told to call has one definition.
    """
    return f"{get_lab_base_url()}/{MCP_ROUTE_PATH}"


def _get_allowed_hosts(mcp_url: str) -> list[str]:
    """Host headers the MCP endpoint answers to.

    The SDK's DNS-rebinding protection rejects any Host it was not told about with
    ``421 Invalid Host header``, so the lab's own domain has to be declared or no
    client can connect (see ``_build_transport_security``).

    The host is derived from the lab's configured URL, which is by definition the
    one clients are told to call. A reverse proxy that rewrites Host would need
    that value added here too.
    """
    host = urlparse(mcp_url).netloc
    return [host] if host else []


class McpServerHolder:
    """Holds the MCP server built at startup.

    The server cannot be built at import time (its URLs come from ``Settings``,
    which is not loaded yet), so something must hold it between ``mount_mcp_app``
    and the app's lifespan. A class attribute rather than a module global: the
    ``global`` statement makes every reader guess whether the name was rebound,
    and ``clear()`` gives tests a way to reset it. Mirrors ``OAuthService``.
    """

    _server: FastMCP | None = None

    @classmethod
    def set_server(cls, server: FastMCP) -> None:
        cls._server = server

    @classmethod
    def get_server_or_none(cls) -> FastMCP | None:
        """Return the server, or ``None`` when MCP was never mounted."""
        return cls._server

    @classmethod
    def clear(cls) -> None:
        """Drop the server. Useful for tests."""
        cls._server = None


@asynccontextmanager
async def mcp_session_manager_lifespan() -> AsyncIterator[None]:
    """Run the MCP session manager for the lifetime of the lab app.

    The manager holds the task group backing MCP sessions. ``streamable_http_app``
    starts it from the sub-app's own lifespan, but Starlette never runs the
    lifespan of a *mounted* sub-app -- so the lab's root app must run it here, or
    every authenticated MCP call fails with "Task group is not initialized".

    A no-op when the MCP server was not mounted (e.g. tests that build their own).
    """
    server = McpServerHolder.get_server_or_none()
    if server is None:
        yield
        return

    async with server.session_manager.run():
        yield



# ---------------------------------------------------------------------- #
#  The MCP app
# ---------------------------------------------------------------------- #


def mount_mcp_app(main_app: FastAPI) -> None:
    """Build the MCP server, register it as a lab sub-app, and expose its metadata.

    Called at startup, before the apps are mounted, because the OAuth issuer and
    resource URLs come from ``Settings``, which is not loaded at import time.

    :param main_app: The lab's root FastAPI app, needed because the OAuth
        discovery documents must be served from the domain root (see
        :func:`_add_well_known_routes`).
    """
    mcp_url = get_mcp_url()

    oauth_provider = LabOAuthProvider(
        consent_page_url=OAuthService.get_consent_page_url(),
        resource_url=mcp_url,
        resource_name=MCP_RESOURCE_NAME,
        lab_url=get_lab_base_url(),
    )
    # OAuthService owns the provider: the consent route reaches it from there,
    # without the OAuth package having to depend on this MCP module.
    OAuthService.set_provider(oauth_provider)

    auth_settings = AuthSettings(
        issuer_url=AnyHttpUrl(mcp_url),
        resource_server_url=AnyHttpUrl(mcp_url),
        client_registration_options=ClientRegistrationOptions(enabled=True),
    )

    mcp_server = build_mcp_server(
        auth_provider=oauth_provider,
        auth_settings=auth_settings,
        allowed_hosts=_get_allowed_hosts(mcp_url),
    )

    # Serve the MCP endpoint at the mount root: the sub-app is mounted at "/mcp/",
    # so the SDK's own path must not repeat it.
    mcp_server.settings.streamable_http_path = "/"

    # The app's lifespan needs it later, to run the session manager.
    McpServerHolder.set_server(mcp_server)

    mcp_app = ApiRegistry.register_api(
        f"/{MCP_ROUTE_PATH}/",
        with_exception_handlers=False,
        with_security_headers=False,
    )
    mcp_app.mount("/", mcp_server.streamable_http_app())

    _add_well_known_routes(main_app, auth_settings)

    Logger.info(f"MCP server available at {mcp_url}")


def _authorization_server_metadata_paths(issuer_url: AnyHttpUrl) -> list[str]:
    """Return every path a client may fetch the authorization-server metadata from.

    Our issuer carries a path (``https://<lab>/mcp``). RFC 8414 §3.1 says a client
    must then insert the well-known segment *between the host and that path* and
    request ``/.well-known/oauth-authorization-server/mcp`` -- which is what
    Claude does. The SDK, however, hardcodes its route at the bare
    ``/.well-known/oauth-authorization-server`` regardless of the issuer, so the
    two disagree and the login dies on a 404 (``{"detail":"Not Found"}``) before
    the browser ever opens.

    Both paths are therefore served: the RFC-compliant one for spec-following
    clients, and the bare one for clients that ignore the issuer path.
    """
    path = urlparse(str(issuer_url)).path.rstrip("/")

    paths = ["/.well-known/oauth-authorization-server"]
    if path:
        paths.insert(0, f"/.well-known/oauth-authorization-server{path}")
    return paths


def _add_well_known_routes(main_app: FastAPI, auth_settings: AuthSettings) -> None:
    """Serve the OAuth discovery documents from the domain root.

    RFC 9728 puts the protected-resource metadata at
    ``/.well-known/oauth-protected-resource/<path>`` -- at the **root** of the
    host, not under the resource's own path. The SDK advertises exactly that URL
    in its ``WWW-Authenticate`` header, but the routes it generates live inside
    the MCP app, which the lab mounts at ``/mcp/``. Left alone they would answer
    on ``/mcp/.well-known/...`` while the client fetches ``/.well-known/...`` and
    gets a 404, so discovery -- and the whole login -- would never start.

    The routes are therefore re-registered on the root app, where the client
    actually looks. The MCP mount does not shadow them: it only claims ``/mcp/``.
    """
    resource_server_url = auth_settings.resource_server_url
    if resource_server_url is None:
        raise ValueError("The MCP auth settings must define a resource server URL")

    routes = create_protected_resource_routes(
        resource_url=resource_server_url,
        authorization_servers=[auth_settings.issuer_url],
        resource_name="Constellab lab MCP server",
    )

    # The authorization-server metadata is likewise fetched from the root. Its
    # endpoints (authorize/token/register) still point into the MCP mount, since
    # build_metadata derives them from the issuer URL (.../mcp).
    metadata = build_metadata(
        issuer_url=auth_settings.issuer_url,
        service_documentation_url=auth_settings.service_documentation_url,
        client_registration_options=auth_settings.client_registration_options
        or ClientRegistrationOptions(enabled=True),
        revocation_options=auth_settings.revocation_options or RevocationOptions(),
    )
    handler = cors_middleware(MetadataHandler(metadata).handle, ["GET", "OPTIONS"])

    for path in _authorization_server_metadata_paths(auth_settings.issuer_url):
        routes.append(Route(path, endpoint=handler, methods=["GET", "OPTIONS"]))

    for route in routes:
        main_app.router.routes.append(route)
