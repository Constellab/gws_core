# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from ...dto.user_dto import UserData
from ...service.progress_bar_service import ProgressBarService
from ._auth_user import check_user_access_token
from .core_app import core_app

@core_app.get("/progress-bar/{uri}", tags=["Progress bar"], summary="Get a progress bar")
async def get_a_progress_bar(uri: str, \
                             _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a progress bar
    
    - **uri**: the uri of the progress bar
    """
        
    p = ProgressBarService.fetch_progress_bar(uri=uri)
    return p.to_json()
