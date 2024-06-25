from fastapi import Depends

from gws_core.lab.monitor.monitor_dto import (MonitorBetweenDateGraphicsDTO,
                                              MonitorDTO)

from ...core_controller import core_app
from ...user.auth_service import AuthService
from .monitor_dto import GetMonitorRequestDTO
from .monitor_service import MonitorService


@core_app.get("/monitor/current", tags=["Lab"], summary="Get current monitor data")
def get_the_last_lab_monitor_data(_=Depends(AuthService.check_user_access_token)) -> MonitorDTO:
    """
    Get current monitor data
    """
    return MonitorService.get_current_monitor_data()


@core_app.post("/monitor/graphics", tags=["Lab"], summary="Get the lab monitor graphics")
def get_the_lab_monitor_graphics(
        request: GetMonitorRequestDTO,
        _=Depends(AuthService.check_user_access_token)) -> MonitorBetweenDateGraphicsDTO:
    """
    Get lab monitor graphics
    """
    timezone_num = request.timezone_number if request.timezone_number else 0
    return MonitorService.get_monitor_graphics_between_dates_str(
        from_date_str=request.from_date, to_date_str=request.to_date, utc_num=timezone_num)
