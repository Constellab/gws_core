# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from .core_app import core_app
from ._auth_user import UserData, check_user_access_token

@core_app.post("/run/astro-travel-experiment", tags=["Astro boy travels"])
async def run_astro_travel_experiment(_: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run astrobot experiment. The default study is used.
    """
    
    from gws.service.astro_service import AstroService
    
    return await AstroService.run_robot_travel()

@core_app.post("/run/astro-super-travel-experiment", tags=["Astro boy travels"])
async def run_astro_super_travel_experiment(_: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run astrobot experiment. The default study is used.
    """
    
    from gws.service.astro_service import AstroService
    
    return await AstroService.run_robot_super_travel()