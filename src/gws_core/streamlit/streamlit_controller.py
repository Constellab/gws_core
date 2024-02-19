# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from fastapi import Depends

from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_dto import StreamlitStatusDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.get("/streamlit/status", tags=["Streamlit"],
              summary="Get streamlit apps status")
def get_streamlit_app_status(_=Depends(AuthService.check_user_access_token)) -> StreamlitStatusDTO:
    """
    Get streamlit apps status
    """

    return StreamlitAppManager.get_status_dto()


@core_app.post("/streamlit/stop", tags=["Streamlit"],
               summary="Stop main streamlit app")
def stop_main_streamlit_app(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Stop the main streamlit app
    """

    return StreamlitAppManager.stop_main_app()
