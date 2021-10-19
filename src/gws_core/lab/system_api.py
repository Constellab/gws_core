

from fastapi.param_functions import Depends

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .system_service import SystemService


@core_app.post("/system/dev-reset", tags=["System"], summary="Reset dev environment")
async def get_the_lab_monitor_data(_: UserData = Depends(AuthService.check_user_access_token)) -> None:
    """
    Reset dev environment
    """

    SystemService.reset_dev_envionment()


@core_app.post("/system/kill", tags=["System"], summary="Stop the python process and the API")
async def kill_process(_: UserData = Depends(AuthService.check_user_access_token)) -> None:
    SystemService.kill_process()
