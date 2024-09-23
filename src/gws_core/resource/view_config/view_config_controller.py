

from typing import List, Optional

from fastapi.param_functions import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_dto import CallViewResultDTO, ViewTypeDTO
from gws_core.resource.view_config.view_config_dto import ViewConfigDTO
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.user.auth_service import AuthService

from ...core_controller import core_app


@core_app.get("/view-config/{id_}", tags=["View config"],
              summary="Get view config")
def get_by_id(id_: str,
              _=Depends(AuthService.check_user_access_token)) -> ViewConfigDTO:
    return ViewConfigService.get_by_id(id_).to_dto()


@core_app.post("/view-config/{id_}/call", tags=["View config"],
               summary="Call a view from a config")
def call_view_config(id_: str,
                     _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:
    return ResourceService.call_view_from_view_config(id_).to_dto()


@core_app.put("/view-config/{id_}/title", tags=["View config"],
              summary="Update the title of a view config")
def update_title(id_: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ViewConfigDTO:
    return ViewConfigService.update_title(id_, body["title"]).to_dto()


@core_app.put("/view-config/{id_}/favorite", tags=["View config"],
              summary="Update the favorite of a view config")
def update_favorite(id_: str,
                    body: dict,
                    _=Depends(AuthService.check_user_access_token)) -> ViewConfigDTO:
    return ViewConfigService.update_favorite(id_, body["is_favorite"]).to_dto()


@core_app.get("/view-config/resource/{resource_id}/favorite/{favorite}", tags=["View config"],
              summary="Get the list of view config by resource")
def get_by_resource(resource_id: str,
                    favorite: bool,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ViewConfigDTO]:
    return ViewConfigService.get_by_resource(
        resource_id=resource_id,
        favorite=favorite,
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


@core_app.post("/view-config/search/note/{note_id}", tags=["View config"],
               summary="Search available view config for a note")
def search_for_note(note_id: str,
                    search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ViewConfigDTO]:
    return ViewConfigService.search_by_note(note_id, search_dict,
                                            page, number_of_items_per_page).to_dto()

############################# VIEW TYPE  ###########################


@core_app.get("/view-config/types/list", tags=["View type"],
              summary="Get all the view types")
def get_view_types(_=Depends(AuthService.check_user_access_token)) -> List[ViewTypeDTO]:
    return ViewConfigService.get_all_view_types()
