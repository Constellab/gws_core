

from fastapi.param_functions import Depends

from ..core.service.settings_service import SettingsService
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .system_service import SystemService


@core_app.post("/system/dev-reset", tags=["System"], summary="Reset dev environment")
async def dev_reset(_: UserData = Depends(AuthService.check_user_access_token)) -> None:
    """
    Reset dev environment
    """

    SystemService.reset_dev_envionment()


@core_app.post("/system/kill", tags=["System"], summary="Stop the python process and the API")
async def kill_process(_: UserData = Depends(AuthService.check_user_access_token)) -> None:
    SystemService.kill_process()


@core_app.get("system/settings", summary="Get settings")
async def get_settings(_: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return SettingsService.get_settings().to_json()
