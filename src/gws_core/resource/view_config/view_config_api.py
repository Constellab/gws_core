# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional

from fastapi.param_functions import Depends
from gws_core.core.classes.paginator import PaginatorDict
from gws_core.core.classes.search_builder import SearchParams
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.tag.tag import Tag
from gws_core.tag.tag_service import TagService
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from ...core_app import core_app


@core_app.get("/view-config/{id}", tags=["View config"],
              summary="Get view config")
def get_by_id(id: str,
              _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.get_by_id(id).to_json(deep=True)


@core_app.post("/view-config/{id}/call", tags=["View config"],
               summary="Call a view from a config")
async def call_view_config(id: str,
                           _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return await ResourceService.call_view_from_view_config(id)


@core_app.put("/view-config/{id}/title", tags=["View config"],
              summary="Update the title of a view config")
def update_title(id: str,
                 body: dict,
                 _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.update_title(id, body["title"]).to_json(deep=True)


@core_app.put("/view-config/{id}/flagged", tags=["View config"],
              summary="Update the flagged of a view config")
def update_flagged(id: str,
                   body: dict,
                   _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.update_flagged(id, body["flagged"]).to_json(deep=True)

@core_app.get("/view-config/resource/{resource_id}", tags=["View config"],
              summary="Get the list of view config by resource")
def get_by_input_resource(resource_id: str,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve a list of experiments by the input resource
    """

    return ViewConfigService.get_by_resource(
        resource_id=resource_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


###################################### SEARCH #######################################


@core_app.post("/view-config/search", tags=["View config"],
               summary="Search available view config")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.search(search_dict,
                                    page, number_of_items_per_page).to_json()


@core_app.post("/view-config/search/report/{report_id}", tags=["View config"],
               summary="Search available view config for a report")
def search_for_report(report_id: str,
                      search_dict: SearchParams,
                      page: Optional[int] = 1,
                      number_of_items_per_page: Optional[int] = 20,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.search_for_report(report_id, search_dict,
                                               page, number_of_items_per_page).to_json()


############################# TAGS ###########################


@core_app.put("/view-config/{id}/tags", tags=["View config"], summary="Update view config tags")
def save_tags(id: str,
              tags: List[Tag],
              _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return TagService.save_tags_to_entity(ViewConfig, id, tags)