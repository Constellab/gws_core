# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.dto.user_dto import UserData
from fastapi import Depends
from typing import Optional

from ._auth_user import check_user_access_token
from .core_app import core_app
from gws.service.lab_service import LabService

@core_app.get("/lab/monitor", tags=["Lab"], summary="Get the lab monitor data")
async def get_the_lab_monitor_data(page: Optional[int] = 1, \
                               number_of_items_per_page: Optional[int] = 20,\
                               _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Get lab monitor    
    """

    return LabService.get_lab_monitor_data(as_json=True)