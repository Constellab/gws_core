from fastapi import Depends
from fastapi.responses import FileResponse, StreamingResponse

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.log.log_dto import LogCompleteInfoDTO, LogsStatusDTO
from gws_core.user.authorization_service import AuthorizationService

from ...core_controller import core_app
from .log_service import LogService


@core_app.get("/log/status", tags=["Log"], summary="Get information about the logs")
def get_logs_status(_=Depends(AuthorizationService.check_user_access_token)) -> LogsStatusDTO:
    return LogService.get_logs_status()


@core_app.get("/log/{log_file_name}", tags=["Log"], summary="Get the content of a log file")
def get_log_complete_info(
    log_file_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> LogCompleteInfoDTO:
    return LogService.get_log_complete_info(log_file_name).to_dto()


@core_app.get("/log/{log_file_name}/download", tags=["Log"], summary="Download a log file")
def download_log(
    log_file_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> FileResponse:
    log_file_path = LogService.get_log_file_path(log_file_name)

    return FileHelper.create_file_response(log_file_path, media_type="text/plain")


@core_app.get(
    "/log/{log_file_name}/download/json", tags=["Log"], summary="Download a log file a json file"
)
def download_log_json(
    log_file_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> StreamingResponse:
    log = LogService.get_log_complete_info(log_file_name)

    return ResponseHelper.create_file_response_from_json(
        log.get_content_as_json(),
        file_name=log.log_info.name + ".json",
        media_type="application/json",
    )
