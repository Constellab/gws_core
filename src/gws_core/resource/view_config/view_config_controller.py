# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi.param_functions import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.resource.view_config.view_config_dto import ViewConfigDTO
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.user.auth_service import AuthService

from ...core_controller import core_app


@core_app.get("/view-config/{id}", tags=["View config"],
              summary="Get view config")
def get_by_id(id: str,
              _=Depends(AuthService.check_user_access_token)) -> ViewConfigDTO:
    return ViewConfigService.get_by_id(id).to_dto()


@core_app.post("/view-config/{id}/call", tags=["View config"],
               summary="Call a view from a config")
def call_view_config(id: str,
                     _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:
    return ResourceService.call_view_from_view_config(id).to_dto()


@core_app.put("/view-config/{id}/title", tags=["View config"],
              summary="Update the title of a view config")
def update_title(id: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ViewConfigDTO:
    return ViewConfigService.update_title(id, body["title"]).to_dto()


@core_app.put("/view-config/{id}/flagged", tags=["View config"],
              summary="Update the flagged of a view config")
def update_flagged(id: str,
                   body: dict,
                   _=Depends(AuthService.check_user_access_token)) -> ViewConfigDTO:
    return ViewConfigService.update_flagged(id, body["flagged"]).to_dto()


@core_app.get("/view-config/resource/{resource_id}/flag/{flagged}", tags=["View config"],
              summary="Get the list of view config by resource")
def get_by_resource(resource_id: str,
                    flagged: bool,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ViewConfigDTO]:
    return ViewConfigService.get_by_resource(
        resource_id=resource_id,
        flagged=flagged,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_dto()


###################################### SEARCH #######################################
@core_app.post("/view-config/search", tags=["View config"],
               summary="Search available view config")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[ViewConfigDTO]:
    return ViewConfigService.search(search_dict,
                                    page, number_of_items_per_page).to_dto()


@core_app.post("/view-config/search/report/{report_id}", tags=["View config"],
               summary="Search available view config for a report")
def search_for_report(report_id: str,
                      search_dict: SearchParams,
                      page: Optional[int] = 1,
                      number_of_items_per_page: Optional[int] = 20,
                      _=Depends(AuthService.check_user_access_token)) -> PageDTO[ViewConfigDTO]:
    return ViewConfigService.search_by_report(report_id, search_dict,
                                              page, number_of_items_per_page).to_dto()