# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/config/list", tags=["Configs"], summary="Get the list of configs")
async def get_list_of_configs(page: int = 1, \
                              number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of configs. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page. 
    """

    from gws.service.config_service import ConfigService
    
    return ConfigService.fetch_config_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
    )
