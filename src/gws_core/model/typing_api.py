from typing import Optional

from fastapi.param_functions import Depends
from gws_core.core.classes.jsonable import ListJsonable
from gws_core.core.classes.search_builder import SearchDict
from gws_core.model.typing_service import TypingService
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from ..core_app import core_app


@core_app.get("/typing/{typing_name}", tags=["Typing"], summary="Get a typing")
async def get_typing(typing_name: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return TypingService.get_typing(typing_name).to_json(deep=True)


@core_app.post("/typing/advanced-search", tags=["Typing"], summary="Search typings")
async def advanced_search(search_dict: SearchDict,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search for typing
    """

    return TypingService.search(search_dict, page, number_of_items_per_page).to_json()


@core_app.get(
    "/typing/transformers/{related_resource_typing_name}", tags=["Task"],
    summary="Get trasnformers related to a resource")
async def get_task_transformers_by_related_resource(related_resource_typing_name: str,
                                                    _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Get tasks types related to a resource
    """

    return ListJsonable(
        TypingService.get_task_transformers_by_related_resource(related_resource_typing_name)).to_json(
        deep=True)  # TODO check deep=True