from datetime import datetime

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse, StreamingResponse

from gws_core.apps.app_dto import (
    AppGatewayHandoffDTO,
    AppGatewayHandoffResponseDTO,
    AppGatewayStartDTO,
    AppGatewayStartResponseDTO,
    AppProcessLightStatusDTO,
    AppsStatusDTO,
    AppStopPolicy,
    ExchangeAppCodeDTO,
    ExchangeAppCodeResponseDTO,
    ValidateAppJwtDTO,
    ValidateAppJwtResponseDTO,
)
from gws_core.apps.app_gateway_service import AppGatewayService
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.apps_manager import AppsManager
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.lab.log.log import LogsBetweenDates
from gws_core.lab.log.log_dto import LogsBetweenDatesDTO

from ..core_controller import core_app
from ..user.authorization_service import AuthorizationService


@core_app.get("/apps/status", tags=["App"], summary="Get apps status")
def get_all_apps_status(_=Depends(AuthorizationService.check_user_access_token)) -> AppsStatusDTO:
    """
    Get app apps status
    """

    return AppsManager.get_status_dto()


@core_app.post("/apps/stop", tags=["App"], summary="Stop all apps")
def stop_all_processes(_=Depends(AuthorizationService.check_user_access_token)) -> None:
    """
    Stop all apps
    """

    return AppsManager.stop_all_processes()


@core_app.post("/apps/stop/{id_}", tags=["App"], summary="Stop main app")
def stop_process(id_: str, _=Depends(AuthorizationService.check_user_access_token)) -> None:
    """
    Stop the app
    """

    return AppsManager.stop_process(id_)


@core_app.put(
    "/apps/{id_}/stop-policy/{stop_policy}",
    tags=["App"],
    summary="Set the stop policy for an app",
)
def set_stop_policy(
    id_: str, stop_policy: AppStopPolicy, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    """
    Set the stop policy on an app.
    With MANUAL, the app will not be automatically stopped when no connections are detected.
    """

    return AppsManager.set_stop_policy(id_, stop_policy)


@core_app.put(
    "/apps/{id_}/custom-subdomain/{subdomain}",
    tags=["App"],
    summary="Set the custom subdomain for an app",
)
def set_custom_subdomain(
    id_: str, subdomain: str, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    """
    Set a readable, stable custom subdomain for an app.
    The value is validated as a DNS label and must be unique across all apps in the lab.
    The custom host is added as a front-only alias next to the id-based host. It is applied
    immediately if the app is running, otherwise on its next start.
    """

    return AppsManager.set_custom_subdomain(id_, subdomain)


@core_app.delete(
    "/apps/{id_}/custom-subdomain",
    tags=["App"],
    summary="Clear the custom subdomain for an app",
)
def clear_custom_subdomain(
    id_: str, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    """
    Clear the custom subdomain of an app, restoring the default id-based host.
    """

    return AppsManager.set_custom_subdomain(id_, None)


@core_app.get("/apps/process/{token}/status", tags=["App"], summary="Get app status by ID")
def get_app_status_by_id(token: str) -> AppProcessLightStatusDTO:
    """
    Get the status of a specific app by its process token.

    The token is an opaque process handle (not a user credential), so this returns only the
    lifecycle fields (id / status / status_text) — no user, config, or env details. See
    APP_AUTH_OAUTH_REDESIGN.md.
    """

    app_process = AppsManager.find_process_by_token(token)

    if app_process is None:
        raise Exception("Invalid token")

    return app_process.get_light_status_dto()


@core_app.post("/apps/exchange-code", tags=["App"], summary="Exchange an app code for a JWT")
def exchange_app_code(data: ExchangeAppCodeDTO) -> ExchangeAppCodeResponseDTO:
    """
    Exchange a one-time app code (the ``gws_code`` the app received in its URL) for a JWT.

    Called by the app itself (reflex/streamlit base), which cannot consume the code or mint a
    JWT (it does not import gws_core). No user-auth dependency: the single-use code is the
    credential. The code is consumed here and must match the app it was minted for.
    """

    return AppsManager.exchange_app_code(data.app_id, data.code)


@core_app.post("/apps/validate-jwt", tags=["App"], summary="Validate an app session JWT")
def validate_app_jwt(data: ValidateAppJwtDTO) -> ValidateAppJwtResponseDTO:
    """
    Validate the JWT an app stored in its ``gws_app_jwt`` cookie and return the user id.

    Called by the app on a fresh page load (F5 / new tab), when there is no one-time code but the
    cookie holds the JWT from the initial handoff. No user-auth dependency: the JWT is the
    credential (validated here). Lets the app re-authenticate without going back through the
    gateway. The app cannot validate the JWT itself (no gws_core, no secret).
    """

    return AppsManager.validate_app_jwt(data.app_id, data.jwt)


# The "nginx-login" segment mirrors AppGatewayService.NGINX_LOGIN_ENDPOINT_SEGMENT (used by
# AppProcess.get_nginx_login_url to build the URL nginx proxies to); keep the two in sync. The
# "gws_code" query param mirrors AppGatewayService.GWS_CODE_QUERY_PARAM.
@core_app.get("/apps/{app_id}/nginx-login", tags=["App"], summary="App-host login (sets session cookie)", response_model=None)
def app_nginx_login(app_id: str, gws_code: str) -> RedirectResponse:
    """
    App-host login endpoint the app's nginx proxies ``/gws-login`` to.

    Exchanges the one-time ``gws_code`` for a JWT, sets it as an HttpOnly, host-only session
    cookie on the app host, and redirects to the app root. From then on every request (including
    a hard refresh) carries the cookie, so the app re-authenticates by reading it — no code in
    the app URL, and auth survives page reloads.

    The app cannot set an HttpOnly cookie itself (Streamlit can't set cookies; app JS can't set
    HttpOnly), so this runs at the app host via nginx + this endpoint.
    """
    # exchange consumes the single-use code and returns the JWT (raises 403 if invalid/expired)
    exchanged = AppsManager.exchange_app_code(app_id, gws_code)

    # redirect to the app root; the cookie is set on this response so the redirected load has it
    response = RedirectResponse(url="/")
    response.set_cookie(
        AppGatewayService.APP_JWT_COOKIE_NAME,
        value=exchanged.user_access_token,
        httponly=True,
        secure=True,  # works over https and localhost
        samesite="lax",  # sent on the top-level redirect navigation
        # host-only: no domain= so app A cannot read app B's cookie
    )
    return response


############################################ APP LAUNCHER GATEWAY ############################################


@core_app.post(
    "/apps/gateway/start",
    tags=["App"],
    summary="Gateway: authenticate + (cold-)start an app",
)
def gateway_start(data: AppGatewayStartDTO, request: Request) -> AppGatewayStartResponseDTO:
    """
    Called by the front (Angular) gateway page ``/open/app/{app_key}``.

    (Cold-)starts the app and returns the status token the front polls until the app is RUNNING.
    For an AUTHENTICATED app the caller must be authenticated (one-time ``code`` or lab session),
    else a 401 is raised so the front redirects to login; a PUBLIC app is started for anyone.
    """
    return AppGatewayService.start(data.app_key, data.code, request)


@core_app.post(
    "/apps/gateway/handoff",
    tags=["App"],
    summary="Gateway: hand off into a running app",
)
def gateway_handoff(data: AppGatewayHandoffDTO) -> AppGatewayHandoffResponseDTO:
    """
    Called by the front gateway page once the app is RUNNING. Returns the app host URL the front
    navigates the browser to: for an AUTHENTICATED app, carrying a one-time ``?gws_code=…`` bound
    to the caller named by the ``authorize_grant`` from /apps/gateway/start; for a PUBLIC app, the
    bare app URL (anonymous, no code).
    """
    return AppGatewayService.handoff(data.app_key, data.authorize_grant)


@core_app.get(
    "/apps/{app_id}/logs", tags=["App"], summary="Get the log of an app", response_model=None
)
def get_app_logs(
    app_id: str,
    from_page_date: datetime | None = None,
    _=Depends(AuthorizationService.check_user_access_token),
) -> LogsBetweenDatesDTO:
    """
    Get the logs of a specific app by its ID
    """

    return AppsManager.get_logs_of_app(app_id, from_page_date).to_dto()


@core_app.get(
    "/apps/{app_id}/logs/download",
    tags=["App"],
    summary="Download the log of an app",
    response_model=None,
)
def download_app_logs(
    app_id: str, _=Depends(AuthorizationService.check_user_access_token)
) -> StreamingResponse:
    """
    Download the logs of a specific app by its ID
    """

    logs: LogsBetweenDates = AppsManager.get_logs_of_app(app_id)

    return ResponseHelper.create_file_response_from_str(logs.to_str(), "logs.txt")


@core_app.get(
    "/apps/nginx/config",
    tags=["App"],
    summary="Get the nginx configuration file content",
    response_model=None,
)
def get_nginx_config(
    _=Depends(AuthorizationService.check_user_access_token),
) -> StreamingResponse:
    """
    Get the content of the nginx configuration file
    """

    nginx_manager = AppNginxManager.get_instance()
    return ResponseHelper.create_file_response_from_path(nginx_manager.get_nginx_config_file_path())


@core_app.get(
    "/apps/nginx/access-log",
    tags=["App"],
    summary="Get the nginx access log content",
    response_model=None,
)
def get_nginx_access_log(
    _=Depends(AuthorizationService.check_user_access_token),
) -> StreamingResponse:
    """
    Get the content of the nginx access log file
    """

    nginx_manager = AppNginxManager.get_instance()
    return ResponseHelper.create_file_response_from_path(nginx_manager.get_nginx_access_log_path())


@core_app.get(
    "/apps/nginx/error-log",
    tags=["App"],
    summary="Get the nginx error log content",
    response_model=None,
)
def get_nginx_error_log(
    _=Depends(AuthorizationService.check_user_access_token),
) -> StreamingResponse:
    """
    Get the content of the nginx error log file
    """

    nginx_manager = AppNginxManager.get_instance()
    return ResponseHelper.create_file_response_from_path(nginx_manager.get_nginx_error_log_path())
