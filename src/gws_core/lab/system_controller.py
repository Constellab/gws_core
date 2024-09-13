

from typing import List

from fastapi.param_functions import Depends

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.system_dto import (LabInfoDTO, LabSystemConfig, PipPackage,
                                     SettingsDTO)

from ..core.service.settings_service import SettingsService
from ..core_controller import core_app
from ..user.auth_service import AuthService
from .system_service import SystemService


@core_app.get("/system/info", tags=["System"], summary="Get system info")
def system_info(_=Depends(AuthService.check_user_access_token)) -> LabInfoDTO:
    """
    Reset dev environment
    """

    return SystemService.get_lab_info()


@core_app.post("/system/dev-reset", tags=["System"], summary="Reset dev environment")
def dev_reset(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Reset dev environment
    """

    SystemService.reset_dev_envionment()


@core_app.post("/system/kill", tags=["System"], summary="Stop the python process and the API")
def kill_process(_=Depends(AuthService.check_user_access_token)) -> None:
    SystemService.kill_dev_environment()


@core_app.post("/system/garbage-collector",  tags=["System"], summary="Trigger garbage collector")
def garbage_collector(_=Depends(AuthService.check_user_access_token)) -> None:
    SystemService.garbage_collector()


class SynchronizeDTO(BaseModelDTO):
    sync_users: bool
    sync_folders: bool


@core_app.post("/system/synchronize",  tags=["System"], summary="Synchronise info with space")
def synchronize(sync_dto: SynchronizeDTO,
                _=Depends(AuthService.check_user_access_token)) -> None:
    SystemService.synchronize_with_space(sync_users=sync_dto.sync_users, sync_folders=sync_dto.sync_folders)


@core_app.get("/system/settings",  tags=["System"], summary="Get settings")
def get_settings(_=Depends(AuthService.check_user_access_token)) -> SettingsDTO:
    return SettingsService.get_settings().to_dto()


@core_app.get("/system/config",  tags=["System"], summary="Get system config")
def get_pip_packages(_=Depends(AuthService.check_user_access_token)) -> LabSystemConfig:
    return SystemService.get_system_config()
