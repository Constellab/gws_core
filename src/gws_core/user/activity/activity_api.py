# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Dict, Optional

from fastapi import Depends

from gws_core.core.classes.search_builder import SearchParams

from ...core_app import core_app
from ...user.auth_service import AuthService
from .activity_service import ActivityService


@core_app.post("/activity/search", tags=["Activity"], summary="Search for activities")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> Dict:
    """
    Advanced search on experiment
    """
    return ActivityService.search(search_dict, page, number_of_items_per_page).to_json()
