# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.log.log_dto import LogCompleteInfoDTO, LogsStatusDTO
from gws_core.user.auth_service import AuthService

from ...core_controller import core_app
from .log_service import LogService


@core_app.get("/log/status", tags=["Log"],
              summary="Get information about the logs")
def get_logs_status(_=Depends(AuthService.check_user_access_token)) -> LogsStatusDTO:
    return LogService.get_logs_status()


@core_app.get("/log/{log_file_name}", tags=["Log"],
              summary="Get the content of a log file")
def get_log_complete_info(log_file_name: str, _=Depends(AuthService.check_user_access_token)) -> LogCompleteInfoDTO:

    return LogService.get_log_complete_info(log_file_name).to_dto()


@core_app.get("/log/{log_file_name}/download", tags=["Log"],
              summary="Download a log file")
def download_log(log_file_name: str, _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    log_file_path = LogService.get_log_file_path(log_file_name)

    return FileHelper.create_file_response(log_file_path, media_type='text/plain')
