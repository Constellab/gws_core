

from typing import Optional, Any

from fastapi import Depends

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.monitor.monitor_dto import MonitorBetweenDateDTO

from ...core_controller import core_app
from ...user.auth_service import AuthService
from .monitor_service import MonitorService


class GetMonitorRequest(BaseModelDTO):
    from_date: Optional[str]
    to_date: Optional[str]
    timezone_number: Optional[int]


@core_app.post("/monitor", tags=["Lab"], summary="Get the lab monitor data")
def get_the_lab_monitor_data(request: GetMonitorRequest,
                             _=Depends(AuthService.check_user_access_token)) -> Any:
    """
    Get lab monitor
    """

    # Set the timezone utc number
    timezone_num = request.timezone_number if request.timezone_number else 0

    return MonitorService.get_monitor_data_between_dates_str(
        from_date_str=request.from_date, to_date_str=request.to_date, utc_num=timezone_num)
