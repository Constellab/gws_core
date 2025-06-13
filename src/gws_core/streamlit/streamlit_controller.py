
from fastapi import Depends

from gws_core.apps.app_dto import AppsStatusDTO
from gws_core.apps.apps_manager import AppsManager

from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.get("/streamlit/status", tags=["Streamlit"],
              summary="Get streamlit apps status")
def get_streamlit_app_status(_=Depends(AuthService.check_user_access_token)) -> AppsStatusDTO:
    """
    Get streamlit apps status
    """

    return AppsManager.get_status_dto()


@core_app.post("/streamlit/stop", tags=["Streamlit"],
               summary="Stop main streamlit app")
def stop_all_processes(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop the main streamlit app
    """

    return AppsManager.stop_all_processes()


@core_app.post("/streamlit/stop/{id}", tags=["Streamlit"],
               summary="Stop main streamlit app")
def stop_process(id: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop the main streamlit app
    """

    return AppsManager.stop_process(id)
