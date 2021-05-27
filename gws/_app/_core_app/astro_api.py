# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.dto.user_dto import UserData
from fastapi import Depends

from .core_app import core_app
from ._auth_user import check_user_access_token
from gws.service.astro_service import AstroService

@core_app.post("/run/astro-travel-experiment", tags=["Astro boy travels"], summary="Run the travel experiment of astro")
async def run_astro_travel_experiment(_: UserData = Depends(check_user_access_token)) -> dict:
    """
    Run astrobot experiment. The default study is used.
    """

    e = await AstroService.run_robot_travel()
    return e.to_json()

@core_app.post("/run/astro-super-travel-experiment", tags=["Astro boy travels"], summary="Run supertravel experiment of astros")
async def run_astro_super_travel_experiment(_: UserData = Depends(check_user_access_token)) -> dict:
    """
    Run astrobot experiment. The default study is used.
    """
    
    e = await AstroService.run_robot_super_travel()
    return e.to_json()