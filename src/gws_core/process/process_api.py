# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from gws_core.core_app import core_app
from gws_core.lab.log.log import LogsBetweenDatesDTO
from gws_core.lab.monitor.monitor_dto import MonitorBetweenDateDTO
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from .process_service import ProcessService, ProcessType


@core_app.get("/process/{process_type}/{id}/logs", tags=["Process"],
              summary="Get the log of a process")
def get_process_logs(process_type: ProcessType,
                     id: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> LogsBetweenDatesDTO:
    """
    Retrieve a list of running experiments.
    """

    return ProcessService.get_logs_of_process(process_type, id).to_json()


@core_app.get("/process/{process_type}/{id}/monitor", tags=["Process"],
              summary="Get the monitoring data of a process")
def get_process_monitors(process_type: ProcessType,
                         id: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> MonitorBetweenDateDTO:
    """
    Retrieve a list of running experiments.
    """

    return ProcessService.get_monitor_of_process(process_type, id).to_json()