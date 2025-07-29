
from fastapi import Depends

from gws_core.apps.app_dto import AppProcessStatusDTO, AppsStatusDTO
from gws_core.apps.apps_manager import AppsManager

from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.get("/apps/status", tags=["App"],
              summary="Get apps status")
def get_all_apps_status(_=Depends(AuthService.check_user_access_token)) -> AppsStatusDTO:
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


@core_app.get("/apps/process/{token}/status", tags=["App"],
              summary="Get app status by ID")
def get_app_status_by_id(token: str) -> AppProcessStatusDTO:
    """
    Get the status of a specific app by its ID
    """

    app_process = AppsManager.find_process_by_token(token)

    if app_process is None:
        raise Exception("Invalid token")

    return app_process.get_status_dto()
