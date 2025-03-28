
from fastapi import Depends

from gws_core.streamlit.streamlit_apps_manager import StreamlitAppsManager
from gws_core.streamlit.streamlit_dto import StreamlitStatusDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.get("/streamlit/status", tags=["Streamlit"],
              summary="Get streamlit apps status")
def get_streamlit_app_status(_=Depends(AuthService.check_user_access_token)) -> StreamlitStatusDTO:
    """
    Get streamlit apps status
    """

    return StreamlitAppsManager.get_status_dto()


@core_app.post("/streamlit/stop", tags=["Streamlit"],
               summary="Stop main streamlit app")
def stop_all_processes(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop the main streamlit app
    """

    return StreamlitAppsManager.stop_all_processes()


@core_app.post("/streamlit/stop/{id}", tags=["Streamlit"],
               summary="Stop main streamlit app")
def stop_process(id: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop the main streamlit app
    """

    return StreamlitAppsManager.stop_process(id)
