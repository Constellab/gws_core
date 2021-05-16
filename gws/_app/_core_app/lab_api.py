# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/lab/instance", tags=["Lab"])
async def get_lab_status(_: UserData = Depends(check_user_access_token)):
    """
    Get lab status
    """
    
    from gws.service.lab_servie import LabService
    
    return LabService.get_lab_status()

@core_app.get("/lab/monitor", tags=["Lab"])
async def get_lab_monitor(page: int = 1, number_of_items_per_page: int = 20,\
                          _: UserData = Depends(check_user_access_token)):
    """
    Get lab monitor    
    """
    
    from gws.service.lab_servie import LabService
    
    return LabService.get_lab_monitor()