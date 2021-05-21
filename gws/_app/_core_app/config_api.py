# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from typing import Optional

from ._auth_user import UserData, check_user_access_token
from .core_app import core_app
from gws.service.config_service import ConfigService

@core_app.get("/config", tags=["Configs"], summary="Get the list of configs")
async def get_the_list_of_configs(search_text: Optional[str] = "",\
                              page: Optional[int] = 1, \
                              number_of_items_per_page: Optional[int] = 20, \
                              _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a list of configs. The list is paginated.

    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page. 
    """

    return ConfigService.fetch_config_list(
        search_text=search_text,
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        as_json = True
    )
