"""Mounts the MCP server (and its OAuth flow) into the lab's FastAPI app.

Serving MCP from the lab process (rather than as a standalone service) reuses the
lab's TLS, domain, and -- critically -- its ``secret_key``, so the JWT the OAuth
flow mints is the very token :class:`JWTService` already validates.

Two apps are registered:

- ``/mcp/``      -- the MCP endpoint itself (Streamable HTTP) plus, courtesy of the
                    SDK, the OAuth discovery documents, ``/register``, ``/authorize``
                    and ``/token``.
- ``/mcp-auth/`` -- the browser-facing callback that finishes the Constellab leg of
                    the flow. It lives outside the MCP app because it is the one
                    part a human's browser actually visits.

Security headers are disabled on ``/mcp/``: it is a machine-to-machine API that no
browser renders (see ``ApiRegistry.register_api``).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

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
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.lab.api_registry import ApiRegistry
from gws_core.mcp.db_mcp import build_mcp_server
from gws_core.mcp.mcp_constellab_login import ConstellabLoginError, ConstellabLoginService
from gws_core.mcp.mcp_oauth_provider import ConstellabOAuthProvider
from gws_core.user.user import User
from gws_core.user.user_service import UserService

MCP_ROUTE_PATH = "mcp"
MCP_AUTH_ROUTE_PATH = "mcp-auth"


def _get_lab_base_url() -> str:
    """Return the lab's externally reachable base URL (no trailing slash)."""
    return Settings.get_lab_api_url().rstrip("/")


def _get_mcp_url() -> str:
    """The canonical MCP resource URL; also the OAuth issuer."""
    return f"{_get_lab_base_url()}/{MCP_ROUTE_PATH}"


def _get_callback_url() -> str:
    """Absolute URL of the route that completes the Constellab login."""
    return f"{_get_lab_base_url()}/{MCP_AUTH_ROUTE_PATH}/callback"


# ---------------------------------------------------------------------- #
#  The browser-facing callback app
# ---------------------------------------------------------------------- #

mcp_auth_app = ApiRegistry.register_api(f"/{MCP_AUTH_ROUTE_PATH}/")

# Both are built lazily by mount_mcp_app: the URLs they need come from Settings,
# which is not loaded at import time.
oauth_provider: ConstellabOAuthProvider | None = None
mcp_server: FastMCP | None = None


def _get_provider() -> ConstellabOAuthProvider:
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


def _resolve_lab_user(email: str) -> User | None:
    """Map a Constellab identity to an active lab user."""
    user = UserService.get_user_by_email(email)
    if user is None or not user.is_active:
        return None
    return user


@mcp_auth_app.get("/callback")
async def mcp_auth_callback(request: Request):
    """Complete the Constellab login leg and redirect back to the MCP client.

    Reached by the user's browser after ``/authorize``. Two phases:

    1. First hit (no ``done`` flag): show a page sending the user to Constellab,
       which polls this same route until the login completes.
    2. Poll hits: check the device code; once Constellab returns a token, resolve
       the identity to a lab user and redirect back to the MCP client with the
       authorization code.
    """
    login_state = request.query_params.get("login_state")
    constellab_auth_url = request.query_params.get("constellab_auth_url")

    if not login_state:
        return HTMLResponse(_error_page("Missing login state. Please restart the login."), 400)

    pending = _get_provider().get_pending_login(login_state)
    if pending is None:
        return HTMLResponse(_error_page("This login session expired. Please retry."), 400)

    # Phase 1: hand the user to Constellab and start polling.
    if request.query_params.get("poll") != "1":
        return HTMLResponse(_login_page(constellab_auth_url or "", login_state))

    # Phase 2: has the user finished logging in on Constellab?
    try:
        constellab_token = ConstellabLoginService.poll_for_token(pending.device_code)
    except ConstellabLoginError as err:
        return HTMLResponse(_error_page(str(err)), 400)

    if constellab_token is None:
        # Still waiting: the page keeps polling.
        return HTMLResponse(_waiting_page(), 202)

    try:
        email = ConstellabLoginService.get_email_from_token(constellab_token)
    except ConstellabLoginError as err:
        return HTMLResponse(_error_page(str(err)), 400)

    user = _resolve_lab_user(email)
    if user is None:
        Logger.info(f"MCP OAuth: refused login for '{email}' (no active lab account)")
        return HTMLResponse(
            _error_page(
                f"The Constellab account '{email}' has no active account on this lab. "
                "Ask a lab administrator for access."
            ),
            403,
        )

    try:
        redirect_url = _get_provider().complete_authorization(login_state, user)
    except Exception as err:
        return HTMLResponse(_error_page(str(err)), 400)

    Logger.info(f"MCP OAuth: authorized '{email}'")
    return RedirectResponse(redirect_url, status_code=302)


def _login_page(constellab_auth_url: str, login_state: str) -> str:
    """Page that opens the Constellab login and polls until it completes."""
    return f"""
    <html><head><title>Connect to the lab</title></head>
    <body style="font-family: sans-serif; max-width: 40rem; margin: 4rem auto;">
      <h2>Connecting to the lab</h2>
      <p>Log in with your Constellab account in the window that just opened.</p>
      <p>If nothing happened,
         <a href="{constellab_auth_url}" target="_blank" rel="noopener">open the login page</a>.</p>
      <p id="status">Waiting for you to finish logging in...</p>
      <script>
        window.open("{constellab_auth_url}", "_blank", "noopener");
        async function poll() {{
          const res = await fetch(
            "?poll=1&login_state={login_state}", {{ redirect: "follow" }});
          if (res.redirected) {{ window.location.href = res.url; return; }}
          if (res.status === 202) {{ setTimeout(poll, 3000); return; }}
          document.body.innerHTML = await res.text();
        }}
        setTimeout(poll, 3000);
      </script>
    </body></html>
    """


def _waiting_page() -> str:
    return "<p>Waiting for you to finish logging in...</p>"


def _error_page(message: str) -> str:
    return f"""
    <html><head><title>Login failed</title></head>
    <body style="font-family: sans-serif; max-width: 40rem; margin: 4rem auto;">
      <h2>Login failed</h2>
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

    oauth_provider = ConstellabOAuthProvider(
        callback_url=_get_callback_url(),
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
    routes.append(
        Route(
            "/.well-known/oauth-authorization-server",
            endpoint=cors_middleware(MetadataHandler(metadata).handle, ["GET", "OPTIONS"]),
            methods=["GET", "OPTIONS"],
        )
    )

    for route in routes:
        main_app.router.routes.append(route)
