from datetime import datetime

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.apps.app_dto import AppProcessStatusDTO, AppsStatusDTO
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


@core_app.get("/apps/process/{token}/status", tags=["App"], summary="Get app status by ID")
def get_app_status_by_id(token: str) -> AppProcessStatusDTO:
    """
    Get the status of a specific app by its ID
    """

    app_process = AppsManager.find_process_by_token(token)

    if app_process is None:
        raise Exception("Invalid token")

    return app_process.get_status_dto()


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
