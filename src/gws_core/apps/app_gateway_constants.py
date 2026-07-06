"""Constants shared across the app launcher gateway / auth flow.

Kept in a dependency-free module (no imports) so low-level consumers — AppProcess,
AppNginxRedirectServiceInfo — can import just the strings at module level, without pulling in
AppGatewayService (and its AppResource / AppsManager / AuthorizationService dependencies) and the
circular imports that would cause. AppGatewayService re-exports these as class attributes for
convenience.

The values are also mirrored as literals in the gws_reflex_base / gws_streamlit_base app modules,
which cannot import gws_core at all (they may run in a virtual env without it). Keep those mirrors
in sync with the values here.
"""

# Name of the host-only, HttpOnly cookie holding the app session JWT. Set by the app-host
# nginx-login endpoint; read by the app (st.context.cookies / reflex request) so auth survives a
# page reload.
APP_JWT_COOKIE_NAME = "gws_app_jwt"

# Query-param name carrying the single-use handoff code in an app URL. The app relays it back to
# the lab (POST /apps/exchange-code) to obtain the session JWT.
GWS_CODE_QUERY_PARAM = "gws_code"

# Path on the app host that nginx proxies to the core-api login endpoint (which exchanges the code
# for a JWT and sets the session cookie). Streamlit handoff targets this path.
GWS_LOGIN_PATH = "gws-login"

# Last URL segment of the core-api app-host login endpoint (…/core-api/apps/{app_id}/nginx-login)
# that the app-host GWS_LOGIN_PATH nginx location proxies to.
NGINX_LOGIN_ENDPOINT_SEGMENT = "nginx-login"
