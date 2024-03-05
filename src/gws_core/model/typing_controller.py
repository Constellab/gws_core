# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Literal, Optional

from fastapi.param_functions import Depends
from pydantic import BaseModel

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.model.typing_dto import TypingDTO, TypingObjectType
from gws_core.model.typing_service import TypingService
from gws_core.protocol.protocol_dto import ProtocolTypingFullDTO
from gws_core.resource.resource_typing_dto import ResourceTypingDTO
from gws_core.task.task_dto import TaskTypingDTO
from gws_core.user.auth_service import AuthService

from ..core_controller import core_app


@core_app.get("/typing/resource/{typing_name}", tags=["Typing"], summary="Get a resource typing")
def get_resource_typing(typing_name: str,
                        _=Depends(AuthService.check_user_access_token)) -> ResourceTypingDTO:
    return TypingService.get_typing(typing_name).to_full_dto()


@core_app.get("/typing/task/{typing_name}", tags=["Typing"], summary="Get a task typing")
def get_task_typing(typing_name: str,
                    _=Depends(AuthService.check_user_access_token)) -> TaskTypingDTO:
    return TypingService.get_typing(typing_name).to_full_dto()


@core_app.get("/typing/protocol/{typing_name}", tags=["Typing"], summary="Get a protocol typing")
def get_protocol_typing(typing_name: str,
                        _=Depends(AuthService.check_user_access_token)) -> ProtocolTypingFullDTO:
    return TypingService.get_typing(typing_name).to_full_dto()


@core_app.get("/typing/object-type/{object_type}", tags=["Resource"],
              summary="Get by object type")
def get_by_object_type(object_type: TypingObjectType,
                       page: Optional[int] = 1,
                       number_of_items_per_page: Optional[int] = 20,
                       _=Depends(AuthService.check_user_access_token)) -> PageDTO[TypingDTO]:

    return TypingService.get_typing_by_object_type(object_type, page, number_of_items_per_page).to_dto()


@core_app.post("/typing/advanced-search", tags=["Typing"], summary="Search typings")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[TypingDTO]:
    """
    Advanced search for typing
    """
    return TypingService.search(search_dict, page, number_of_items_per_page).to_dto()


class SearchWithResourceTypes(BaseModel):
    resource_typing_names: List[str]
    search_params: SearchParams


@core_app.post(
    "/typing/processes/suggestion/{inputs_or_outputs}", tags=["Typing"],
    summary="Search process with specific input type")
def process_with_input_search(search: SearchWithResourceTypes,
                              inputs_or_outputs: Literal['inputs', 'outputs'],
                              page: Optional[int] = 1,
                              number_of_items_per_page: Optional[int] = 20,
                              _=Depends(AuthService.check_user_access_token)) -> PageDTO[TypingDTO]:
    """
    Advanced search for typing
    """
    return TypingService.suggest_process(search.search_params, search.resource_typing_names, inputs_or_outputs,
                                         page, number_of_items_per_page).to_dto()


@core_app.post("/typing/importers/search/{resource_typing_name}/{extension}",
               tags=["Typing"], summary="Search typings")
def importers_advanced_search(search_dict: SearchParams,
                              resource_typing_name: str,
                              extension: str,
                              page: Optional[int] = 1,
                              number_of_items_per_page: Optional[int] = 20,
                              _=Depends(AuthService.check_user_access_token)) -> PageDTO[TypingDTO]:
    """
    Advanced search for importers typing
    """
    return TypingService.search_importers(resource_typing_name, extension,
                                          search_dict, page, number_of_items_per_page).to_dto()


@core_app.post("/typing/transformers/search",
               tags=["Typing"], summary="Search typings")
def transformers_advanced_search(search: SearchWithResourceTypes,
                                 page: Optional[int] = 1,
                                 number_of_items_per_page: Optional[int] = 20,
                                 _=Depends(AuthService.check_user_access_token)) -> PageDTO[TypingDTO]:
    """
    Advanced search for transformers typing
    """
    return TypingService.search_transformers(
        search.resource_typing_names, search.search_params, page, number_of_items_per_page).to_dto()


@core_app.delete("/typing/unavailable", tags=["Typing"],
                 summary="Delete unavailable typings")
def delete_unavailable_typings(_=Depends(AuthService.check_user_access_token)) -> None:
    TypingService.delete_unavailable_typings()


@core_app.delete("/typing/unavailable/{brick_name}", tags=["Typing"],
                 summary="Delete unavailable typings")
def delete_unavailable_typings_for_brick(
        brick_name: str,
        _=Depends(AuthService.check_user_access_token)) -> None:
    TypingService.delete_unavailable_typings(brick_name)
