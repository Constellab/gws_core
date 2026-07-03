from datetime import datetime

from fastapi import Depends, Request
from fastapi.responses import StreamingResponse

from gws_core.apps.app_dto import (
    AppGatewayHandoffDTO,
    AppGatewayHandoffResponseDTO,
    AppGatewayStartDTO,
    AppGatewayStartResponseDTO,
    AppProcessStatusDTO,
    AppsStatusDTO,
    AppStopPolicy,
    ExchangeAppCodeDTO,
    ExchangeAppCodeResponseDTO,
)
from gws_core.apps.app_gateway_service import AppGatewayService
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.apps_manager import AppsManager
from gws_core.core.exception.exceptions.unauthorized_exception import UnauthorizedException
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.lab.log.log import LogsBetweenDates
from gws_core.lab.log.log_dto import LogsBetweenDatesDTO
from gws_core.user.user import User

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
def get_app_status_by_id(token: str) -> AppProcessStatusDTO:
    """
    Get the status of a specific app by its ID
    """

    app_process = AppsManager.find_process_by_token(token)

    if app_process is None:
        raise Exception("Invalid token")

    return app_process.get_status_dto()


@core_app.post("/apps/exchange-code", tags=["App"], summary="Exchange an app code for a JWT")
def exchange_app_code(data: ExchangeAppCodeDTO) -> ExchangeAppCodeResponseDTO:
    """
    Exchange a one-time app code (the ``gws_code`` the app received in its URL) for a JWT.

    Called by the app itself (reflex/streamlit base), which cannot consume the code or mint a
    JWT (it does not import gws_core). No user-auth dependency: the single-use code is the
    credential. The code is consumed here and must match the app it was minted for.
    """

    return AppsManager.exchange_app_code(data.app_id, data.code)


############################################ APP LAUNCHER GATEWAY ############################################


def _resolve_gateway_user(request: Request, code: str | None) -> User | None:
    """Resolve the caller for the launcher gateway from either a one-time code or a lab session.

    Model B: if a ``code`` is present it is consumed directly (no lab session minted); otherwise
    the lab session token (cookie/header) is tried. Returns None when neither identifies a user,
    so the gateway can bounce to the auth page.
    """
    if code:
        return AuthorizationService.check_unique_code(code).get_user()

    has_auth_header = request.headers.get("Authorization")
    has_auth_cookie = request.cookies.get("Authorization")
    print(f"[GWS DEBUG] _resolve_gateway_user: no code. "
          f"Authorization header={has_auth_header!r} cookie={has_auth_cookie!r} "
          f"all_cookies={list(request.cookies.keys())!r}")
    try:
        user = AuthorizationService.check_user_access_token(request).get_user()
        print(f"[GWS DEBUG] _resolve_gateway_user resolved user={user.id if user else None!r}")
        return user
    except Exception as e:
        print(f"[GWS DEBUG] _resolve_gateway_user no user: {e!r}")
        return None


@core_app.post(
    "/apps/gateway/start",
    tags=["App"],
    summary="Gateway: authenticate + (cold-)start an app",
)
def gateway_start(data: AppGatewayStartDTO, request: Request) -> AppGatewayStartResponseDTO:
    """
    Called by the front (Angular) gateway page ``/open/app/{app_key}``.

    Resolves the caller (one-time ``code`` or lab session), (cold-)starts the app, and returns
    the status token the front polls until the app is RUNNING. Raises 401 when the caller is
    not authenticated, so the front redirects to the login page itself.
    """
    print("BBBBBBBBBBBBBBBBBBBBBBBBB")
    app_resource = AppGatewayService.resolve_app_resource(data.app_key)

    user = _resolve_gateway_user(request, data.code)
    if user is None:
        raise UnauthorizedException("User not authenticated")

    status_token = AppGatewayService.start_app_and_get_status_token(app_resource)
    return AppGatewayStartResponseDTO(status_token=status_token)


@core_app.post(
    "/apps/gateway/handoff",
    tags=["App"],
    summary="Gateway: hand off into a running app",
)
def gateway_handoff(data: AppGatewayHandoffDTO, request: Request) -> AppGatewayHandoffResponseDTO:
    """
    Called by the front gateway page once the app is RUNNING. Mints a one-time handoff code and
    returns the app host URL (carrying ``?gws_code=…``) the front navigates the browser to. The
    user is resolved from the lab session established for this browser.
    """
    print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    app_resource = AppGatewayService.resolve_app_resource(data.app_key)

    user = _resolve_gateway_user(request, None)
    if user is None:
        raise UnauthorizedException("User not authenticated")

    app_url = AppGatewayService.build_app_handoff_url(app_resource, user)
    return AppGatewayHandoffResponseDTO(app_url=app_url)


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
