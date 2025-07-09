
from fastapi import Depends

from gws_core.apps.app_dto import AppsStatusDTO
from gws_core.apps.apps_manager import AppsManager

from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.get("/apps/status", tags=["App"],
              summary="Get apps status")
def get_app_status(_=Depends(AuthService.check_user_access_token)) -> AppsStatusDTO:
    """
    Get app apps status
    """

    return AppsManager.get_status_dto()


@core_app.post("/apps/stop", tags=["App"],
               summary="Stop all apps")
def stop_all_processes(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop all apps
    """

    return AppsManager.stop_all_processes()


@core_app.post("/apps/stop/{id_}", tags=["App"],
               summary="Stop main app")
def stop_process(id_: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop the app
    """

    return AppsManager.stop_process(id_)
