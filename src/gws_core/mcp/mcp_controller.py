"""Mounts the MCP server (and its OAuth flow) into the lab's FastAPI app.

Serving MCP from the lab process (rather than as a standalone service) reuses the
lab's TLS, domain, and -- critically -- its ``secret_key``, so the JWT the OAuth
flow mints is the very token :class:`JWTService` already validates.

Two apps are registered:

- ``/mcp/``      -- the MCP endpoint itself (Streamable HTTP) plus, courtesy of the
                    SDK, the OAuth discovery documents, ``/register``, ``/authorize``
                    and ``/token``.
- ``/mcp-auth/`` -- the browser-facing route that completes an authorization once
                    the user has consented on the lab front-end. It lives outside
                    the MCP app because it is the one part a human's browser
                    actually visits.

The consent UI itself is a lab front-end page (``docs/todo/mcp_consent_frontend_spec.md``);
the lab API only redirects to it and receives its result.

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
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.lab.api_registry import ApiRegistry
from gws_core.mcp.db_mcp import build_mcp_server
from gws_core.mcp.mcp_oauth_provider import LabOAuthProvider
from gws_core.user.authorization_service import AuthorizationService

MCP_ROUTE_PATH = "mcp"
MCP_AUTH_ROUTE_PATH = "mcp-auth"

# Route of the consent page on the lab front-end. Must match the front-end's
# router (see docs/todo/mcp_consent_frontend_spec.md).
CONSENT_PAGE_ROUTE = "mcp-consent"


def _get_lab_base_url() -> str:
    """Return the lab's externally reachable base URL (no trailing slash)."""
    return Settings.get_lab_api_url().rstrip("/")


def _get_mcp_url() -> str:
    """The canonical MCP resource URL; also the OAuth issuer."""
    return f"{_get_lab_base_url()}/{MCP_ROUTE_PATH}"


def _get_consent_page_url() -> str:
    """Absolute URL of the lab front-end page where the user approves a client.

    Implemented by the front-end (see ``docs/todo/mcp_consent_frontend_spec.md``);
    the lab only ever redirects to it with a ``login_state``.
    """
    return f"{Settings.get_front_url().rstrip('/')}/{CONSENT_PAGE_ROUTE}"


# ---------------------------------------------------------------------- #
#  The browser-facing callback app
# ---------------------------------------------------------------------- #

mcp_auth_app = ApiRegistry.register_api(f"/{MCP_AUTH_ROUTE_PATH}/")

# Both are built lazily by mount_mcp_app: the URLs they need come from Settings,
# which is not loaded at import time.
oauth_provider: LabOAuthProvider | None = None
mcp_server: FastMCP | None = None


def _get_provider() -> LabOAuthProvider:
    if oauth_provider is None:
        raise RuntimeError("The MCP server is not initialized (mount_mcp_app was not called).")
    return oauth_provider


@asynccontextmanager
async def mcp_session_manager_lifespan() -> AsyncIterator[None]:
    """Run the MCP session manager for the lifetime of the lab app.

    The manager holds the task group backing MCP sessions. ``streamable_http_app``
    starts it from the sub-app's own lifespan, but Starlette never runs the
    lifespan of a *mounted* sub-app -- so the lab's root app must run it here, or
    every authenticated MCP call fails with "Task group is not initialized".

    A no-op when the MCP server was not mounted (e.g. tests that build their own).
    """
    if mcp_server is None:
        yield
        return

    async with mcp_server.session_manager.run():
        yield


@mcp_auth_app.get("/consent")
async def mcp_auth_consent(request: Request):
    """Finish an authorization once the user has consented on the front-end.

    The browser arrives here from the lab's consent page (see
    ``docs/todo/mcp_consent_frontend_spec.md``) carrying:

    - ``login_state``: the pending authorization opened by ``/authorize``
    - ``code``: a single-use, 60s code the front-end obtained from
      ``/core-api/user/mcp-consent-code`` while authenticated

    The code **is** the proof of identity: the front-end and this API live on
    different sub-domains and the lab session cookie is ``samesite=strict``, so it
    is never sent here. This is the same bridge the lab already uses for
    ``login-temp-access``.

    Responds with a 302 back to the MCP client, so it must be reached by a real
    browser navigation (not fetch).
    """
    login_state = request.query_params.get("login_state")
    code = request.query_params.get("code")

    if not login_state or not code:
        return HTMLResponse(
            _error_page("This authorization link is incomplete. Please start again from your client."),
            400,
        )

    # Consumes the code: it cannot be replayed.
    try:
        auth_context = AuthorizationService.check_unique_code(code)
    except Exception:
        Logger.info("MCP OAuth: consent refused (invalid or already-used code)")
        return HTMLResponse(
            _error_page("This authorization link has expired or was already used. Please try again."),
            400,
        )

    user = auth_context.get_user()

    try:
        redirect_url = _get_provider().complete_authorization(login_state, user)
    except Exception:
        return HTMLResponse(
            _error_page("This authorization request expired. Please start again from your client."),
            400,
        )

    Logger.info(f"MCP OAuth: authorized '{user.email}'")
    return RedirectResponse(redirect_url, status_code=302)


def _error_page(message: str) -> str:
    return f"""
    <html><head><title>Authorization failed</title></head>
    <body style="font-family: sans-serif; max-width: 40rem; margin: 4rem auto;">
      <h2>Authorization failed</h2>
      <p>{message}</p>
    </body></html>
    """


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
    global oauth_provider, mcp_server

    mcp_url = _get_mcp_url()

    oauth_provider = LabOAuthProvider(
        consent_page_url=_get_consent_page_url(),
        resource_url=mcp_url,
    )

    auth_settings = AuthSettings(
        issuer_url=mcp_url,
        resource_server_url=mcp_url,
        client_registration_options=ClientRegistrationOptions(enabled=True),
    )

    mcp_server = build_mcp_server(auth_provider=oauth_provider, auth_settings=auth_settings)

    # Serve the MCP endpoint at the mount root: the sub-app is mounted at "/mcp/",
    # so the SDK's own path must not repeat it.
    mcp_server.settings.streamable_http_path = "/"

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
    routes = create_protected_resource_routes(
        resource_url=auth_settings.resource_server_url,
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
