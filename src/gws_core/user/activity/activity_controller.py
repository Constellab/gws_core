
from fastapi import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.user.activity.activity_dto import ActivityDTO

from ...core_controller import core_app
from ..authorization_service import AuthorizationService
from .activity_service import ActivityService


@core_app.post("/activity/search", tags=["Activity"], summary="Search for activities")
def advanced_search(
    search_dict: SearchParams,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[ActivityDTO]:
    """
    Advanced search on scenario
    """
    return ActivityService.search(search_dict, page, number_of_items_per_page).to_dto()
