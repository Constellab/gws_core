

from datetime import datetime

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core_controller import core_app
from gws_core.lab.log.log import LogsBetweenDates
from gws_core.lab.log.log_dto import LogsBetweenDatesDTO
from gws_core.lab.monitor.monitor_dto import (GetMonitorTimezoneDTO,
                                              MonitorBetweenDateGraphicsDTO)
from gws_core.user.authorization_service import AuthorizationService

from .process_service import ProcessService, ProcessType


@core_app.get("/process/{process_type}/{id}/logs", tags=["Process"],
              summary="Get the log of a process", response_model=None)
def get_process_logs(process_type: ProcessType,
                     id: str,
                     from_page_date: datetime = None,
                     _=Depends(AuthorizationService.check_user_access_token)) -> LogsBetweenDatesDTO:
    """
    Retrieve a list of running scenarios.
    """

    return ProcessService.get_logs_of_process(process_type, id, from_page_date).to_dto()


@core_app.get("/process/{process_type}/{id}/logs/download", tags=["Process"],
              summary="Download the log of a process", response_model=None)
def download_process_logs(process_type: ProcessType,
                          id: str,
                          _=Depends(AuthorizationService.check_user_access_token)) -> StreamingResponse:
    """
    Retrieve a list of running scenarios.
    """

    logs: LogsBetweenDates = ProcessService.get_logs_of_process(process_type, id)

    return ResponseHelper.create_file_response_from_str(logs.to_str(), "logs.txt")


@core_app.post("/process/{process_type}/{id}/monitor", tags=["Process"],
               summary="Get the monitoring data of a process", response_model=None)
def get_process_monitors(process_type: ProcessType,
                         id: str,
                         body: GetMonitorTimezoneDTO,
                         _=Depends(AuthorizationService.check_user_access_token)) -> MonitorBetweenDateGraphicsDTO:
    """
    Retrieve a list of running scenarios.
    """
    timezone_number = body.timezone_number if body.timezone_number else 0
    return ProcessService.get_monitor_of_process(process_type, id, timezone_number)
