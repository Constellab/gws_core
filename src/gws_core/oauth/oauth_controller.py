"""The browser-facing route that completes an OAuth authorization.

Mounted at ``/oauth-auth/`` rather than inside any protected resource's app: it is
the one part of the flow a human's browser actually visits, and it is shared by
every OAuth client the lab authorizes -- not just MCP.

The consent UI itself is a lab front-end page
(``docs/todo/oauth_consent_frontend_spec.md``); the lab API only redirects to it and
receives its result here.
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from gws_core.core.utils.logger import Logger
from gws_core.lab.api_registry import ApiRegistry
from gws_core.oauth.oauth_service import OAuthService
from gws_core.user.authorization_service import AuthorizationService

OAUTH_AUTH_ROUTE_PATH = "oauth-auth"

oauth_auth_app = ApiRegistry.register_api(f"/{OAUTH_AUTH_ROUTE_PATH}/")


@oauth_auth_app.get("/consent")
async def oauth_consent(request: Request):
    """Finish an authorization once the user has consented on the front-end.

    The browser arrives here from the lab's consent page carrying:

    - ``login_state``: the pending authorization opened by ``/authorize``
    - ``code``: a single-use, 60s code the front-end obtained from
      ``/core-api/user/oauth-consent-code`` while authenticated

    The code **is** the proof of identity: the front-end and this API live on
    different sub-domains and the lab session cookie is ``samesite=strict``, so it
    is never sent here. This is the same bridge the lab already uses for
    ``login-temp-access``.

    Responds with a 302 back to the client, so it must be reached by a real browser
    navigation (not fetch).
    """
    login_state = request.query_params.get("login_state")
    code = request.query_params.get("code")

    if not login_state or not code:
        return HTMLResponse(
            _error_page(
                "This authorization link is incomplete. Please start again from your client."
            ),
            400,
        )

    # Consumes the code: it cannot be replayed.
    try:
        auth_context = AuthorizationService.check_unique_code(code)
    except Exception:
        Logger.info("OAuth: consent refused (invalid or already-used code)")
        return HTMLResponse(
            _error_page(
                "This authorization link has expired or was already used. Please try again."
            ),
            400,
        )

    user = auth_context.get_user()

    try:
        redirect_url = OAuthService.get_provider().complete_authorization(login_state, user)
    except Exception:
        return HTMLResponse(
            _error_page(
                "This authorization request expired. Please start again from your client."
            ),
            400,
        )

    Logger.info(f"OAuth: authorized '{user.email}'")
    return RedirectResponse(redirect_url, status_code=302)


def _error_page(message: str) -> str:
    return f"""
    <html><head><title>Authorization failed</title></head>
    <body style="font-family: sans-serif; max-width: 40rem; margin: 4rem auto;">
      <h2>Authorization failed</h2>
      <p>{message}</p>
    </body></html>
    """
