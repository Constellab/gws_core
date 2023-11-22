# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from fastapi.param_functions import Depends

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.tag_dto import NewTagDTO

from ..core.classes.jsonable import ListJsonable
from ..core_app import core_app
from ..user.auth_service import AuthService
from .tag_service import TagService


@core_app.get("/tag/{key}", tags=["Tag"], summary='Search tag by key')
def search_by_key(key: str,
                  _=Depends(AuthService.check_user_access_token)):
    """
    Search tags by key.
    """

    tags = TagService.search_by_key(key)
    return ListJsonable(tags).to_json()


@core_app.get("/tag", tags=["Tag"], summary='Get all tags')
def get_all(_=Depends(AuthService.check_user_access_token)):

    tags = TagService.get_all_tags()
    return ListJsonable(tags).to_json()


@core_app.post("/tag/{key}/{value}", tags=["Tag"], summary='Register a new tag')
def register_tag(key: str,
                 value: str,
                 _=Depends(AuthService.check_user_access_token)):
    return TagService.register_tag(key, value).to_json()


@core_app.put("/tag/{tag_key}/reorder", tags=["Tag"], summary='Reoarder tags')
def reorder_tag_values(tag_key: str,
                       tags_values: List[str],
                       _=Depends(AuthService.check_user_access_token)):
    return TagService.reorder_tag_values(tag_key, tags_values).to_json()


@core_app.put("/tag/reorder", tags=["Tag"], summary='Reoarder tags')
def reorder_tags(tags_keys: List[str],
                 _=Depends(AuthService.check_user_access_token)):
    return ListJsonable(TagService.reorder_tags(tags_keys)).to_json()


@core_app.put("/tag/{key}/{old_value}/{new_value}", tags=["Tag"], summary='Update registered tag value')
def update_registered_tag_value(key: str,
                                old_value: str,
                                new_value: str,
                                _=Depends(AuthService.check_user_access_token)):
    return TagService.update_registered_tag_value(key, old_value, new_value).to_json()


@core_app.delete("/tag/{key}/{value}", tags=["Tag"], summary='Delete registered tag')
def delete_registered_tag(key: str,
                          value: str,
                          _=Depends(AuthService.check_user_access_token)):
    return TagService.delete_registered_tag(key, value)

################################# ENTITY TAG #################################


@core_app.get("/tag/entity/{entity_type}/{entity_id}", tags=["Tag"], summary='Get tags of an entity')
def get_tags_of_entity(entity_type: EntityType,
                       entity_id: str,
                       _=Depends(AuthService.check_user_access_token)):
    return TagService.find_by_entity_id(entity_type, entity_id).to_json()


@core_app.post(
    "/tag/entity/{entity_type}/{entity_id}/{propagate}", tags=["Tag"],
    summary="Save entity tags")
def add_tag(entity_type: EntityType,
            entity_id: str,
            propagate: bool,
            tags: List[NewTagDTO],
            _=Depends(AuthService.check_user_access_token)) -> list:
    return TagService.add_tag_dict_to_entity(entity_type, entity_id, tags, propagate)


@core_app.delete(
    "/tag/entity/{entity_type}/{entity_id}/{tag_key}/{tag_value}", tags=["Tag"],
    summary="Delete entity tag")
def delete_tag(entity_type: EntityType,
               entity_id: str,
               tag_key: str,
               tag_value: str,
               _=Depends(AuthService.check_user_access_token)) -> None:
    TagService.delete_tag_from_entity(entity_type, entity_id, tag_key, tag_value)


################################### CHECK PROPAGATION ####################################
@core_app.post(
    "/tag/check-propagation-add/{entity_type}/{entity_id}", tags=["Tag"],
    summary="Check tag propagation impact for tags addition")
def check_propagation_add_tags(entity_type: EntityType,
                               entity_id: str,
                               tags: List[NewTagDTO],
                               _=Depends(AuthService.check_user_access_token)) -> dict:
    return TagService.check_propagation_add_tags(entity_type, entity_id, tags).to_json()


@core_app.post(
    "/tag/check-propagation-delete/{entity_type}/{entity_id}", tags=["Tag"],
    summary="Check tag propagation impact for tag deletion")
def check_propagation_delete_tag(entity_type: EntityType,
                                 entity_id: str,
                                 tag: NewTagDTO,
                                 _=Depends(AuthService.check_user_access_token)) -> dict:
    return TagService.check_propagation_delete_tag(entity_type, entity_id, tag).to_json()
