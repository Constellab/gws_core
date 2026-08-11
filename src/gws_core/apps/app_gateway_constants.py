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

# Lifetime of the app JWT cookie. Without it the cookie is a *session* cookie, dropped when the
# browser closes — so the app forgot the visitor long before the 2-day JWT expired, which reads as
# "the app logs me out constantly". Outliving the JWT is deliberate: the JWT stays the real authority
# (validated on every load, and re-minted while the app is in use), the cookie is only its persistent
# store. Mirrored as a literal in gws_reflex_base, which cannot import gws_core.
APP_JWT_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30

# Query-param name carrying the single-use handoff code in an app URL. The app relays it back to
# the lab (POST /apps/exchange-code) to obtain the session JWT.
GWS_CODE_QUERY_PARAM = "gws_code"

# Path on the app host that nginx proxies to the core-api login endpoint (which exchanges the code
# for a JWT and sets the session cookie). Streamlit handoff targets this path.
GWS_LOGIN_PATH = "gws-login"

# Last URL segment of the core-api app-host login endpoint (…/core-api/apps/{app_id}/nginx-login)
# that the app-host GWS_LOGIN_PATH nginx location proxies to.
NGINX_LOGIN_ENDPOINT_SEGMENT = "nginx-login"

# Path on the nginx fallback (`default_server`) block that proxies to the core-api fallback
# resolver. Requests for a host no running app claims are redirected here, so a shared URL of a
# stopped app still gets an answer instead of hitting a dead port.
APP_FALLBACK_PATH = "gws-app-fallback"

# Core-api route (…/core-api/apps/<this>) that maps an app host back to an app key and redirects to
# the Angular gateway, which owns the auth guard, cold-start and progress UI.
APP_FALLBACK_ENDPOINT_SEGMENT = "fallback/resolve"

# Query-param names the fallback block passes to the resolver: the original app host, and the
# original path+query so a deep link survives the trip through the gateway.
APP_FALLBACK_HOST_QUERY_PARAM = "host"
APP_FALLBACK_TARGET_QUERY_PARAM = "target"

# Query-param carrying the in-app path the gateway should land on after handoff, so sharing a deep
# link (e.g. /config) does not drop the user on the app root.
REDIRECT_TO_QUERY_PARAM = "redirect_to"

# Query-param telling the gateway page to render a terminal error instead of trying to open an app.
# The fallback resolver is reached by a top-level browser navigation, so raising an API exception
# there would show the raw JSON error envelope to a human; it redirects with this instead.
GATEWAY_ERROR_QUERY_PARAM = "error"

# Values for GATEWAY_ERROR_QUERY_PARAM. Distinguished because the resolver can tell them apart
# cheaply and they mean different things to the user: a host that is not shaped like an app host at
# all (mistyped/foreign URL) vs a well-formed key whose app is gone (deleted or never existed).
GATEWAY_ERROR_INVALID_HOST = "invalid_host"
GATEWAY_ERROR_APP_NOT_FOUND = "app_not_found"
