from typing import List, Optional

from fastapi.param_functions import Depends
from gws_core.core.classes.search_builder import SearchParams
from gws_core.model.typing_service import TypingService
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData
from pydantic import BaseModel

from ..core_app import core_app


@core_app.get("/typing/{typing_name}", tags=["Typing"], summary="Get a typing")
async def get_typing(typing_name: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return TypingService.get_typing(typing_name).to_json(deep=True)


@core_app.post("/typing/advanced-search", tags=["Typing"], summary="Search typings")
async def advanced_search(search_dict: SearchParams,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search for typing
    """
    return TypingService.search(search_dict, page, number_of_items_per_page).to_json()


@core_app.post("/typing/importers/search/{resource_typing_name}/{extension}",
               tags=["Typing"], summary="Search typings")
async def importers_advanced_search(search_dict: SearchParams,
                                    resource_typing_name: str,
                                    extension: str,
                                    page: Optional[int] = 1,
                                    number_of_items_per_page: Optional[int] = 20,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search for importers typing
    """
    return TypingService.search_importers(resource_typing_name, extension,
                                          search_dict, page, number_of_items_per_page).to_json()


class TransformerSearch(BaseModel):
    resource_typing_names: List[str]
    search_params: SearchParams


@core_app.post("/typing/transformers/search",
               tags=["Typing"], summary="Search typings")
async def transformers_advanced_search(search: TransformerSearch,
                                       page: Optional[int] = 1,
                                       number_of_items_per_page: Optional[int] = 20,
                                       _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search for transformers typing
    """
    return TypingService.search_transformers(
        search.resource_typing_names, search.search_params, page, number_of_items_per_page).to_json()
