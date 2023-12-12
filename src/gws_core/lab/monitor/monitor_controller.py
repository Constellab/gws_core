# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi import Depends
from pydantic import BaseModel

from gws_core.lab.monitor.monitor_dto import MonitorBetweenDateDTO

from ...core_controller import core_app
from ...user.auth_service import AuthService
from .monitor_service import MonitorService


class GetMonitorRequest(BaseModel):
    from_date: Optional[str]
    to_date: Optional[str]


@core_app.post("/monitor", tags=["Lab"], summary="Get the lab monitor data")
def get_the_lab_monitor_data(request: GetMonitorRequest,
                             _=Depends(AuthService.check_user_access_token)) -> MonitorBetweenDateDTO:
    """
    Get lab monitor
    """

    return MonitorService.get_monitor_data_between_dates_str(
        from_date_str=request.from_date, to_date_str=request.to_date)
