# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Optional

from fastapi.param_functions import Depends

from gws_core.core.model.model_dto import PageDTO
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.tag_dto import (EntityTagDTO, EntityTagFullDTO, NewTagDTO,
                                  SaveTagModelResonseDTO, TagKeyModelDTO,
                                  TagPropagationImpactDTO, TagValueModelDTO)

from ..core_app import core_app
from ..user.auth_service import AuthService
from .tag_service import TagService


@core_app.get("/tag/search/key", tags=["Tag"], summary='Search tags by key')
def search_all_keys(page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[TagKeyModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_keys(None, page, number_of_items_per_page).to_dto()


@core_app.get("/tag/search/key/{key}", tags=["Tag"], summary='Search tags by key')
def search_keys(key: Optional[str],
                page: Optional[int] = 1,
                number_of_items_per_page: Optional[int] = 20,
                _=Depends(AuthService.check_user_access_token)) -> PageDTO[TagKeyModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_keys(key, page, number_of_items_per_page).to_dto()


@core_app.get("/tag/search/key/{key}/value", tags=["Tag"], summary='Search tags by value')
def search_all_values(key: str,
                      page: Optional[int] = 1,
                      number_of_items_per_page: Optional[int] = 20,
                      _=Depends(AuthService.check_user_access_token)) -> PageDTO[TagValueModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_values(key, None, page, number_of_items_per_page).to_dto()


@core_app.get("/tag/search/key/{key}/value/{value}", tags=["Tag"], summary='Search tags by value')
def search_values(key: str,
                  value: Optional[str],
                  page: Optional[int] = 1,
                  number_of_items_per_page: Optional[int] = 20,
                  _=Depends(AuthService.check_user_access_token)) -> PageDTO[TagValueModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_values(key, value, page, number_of_items_per_page).to_dto()


@core_app.post("/tag/{key}/{value}", tags=["Tag"], summary='Register a new tag')
def create_tag(key: str,
               value: str,
               _=Depends(AuthService.check_user_access_token)) -> SaveTagModelResonseDTO:
    tag_value_model = TagService.create_tag(key, value)
    return SaveTagModelResonseDTO(
        key_model=tag_value_model.tag_key.to_dto(),
        value_model=tag_value_model.to_dto()
    )


@core_app.put("/tag/reorder", tags=["Tag"], summary='Reoarder tags')
def reorder_tags(tags_keys: List[str],
                 _=Depends(AuthService.check_user_access_token)) -> List[TagKeyModelDTO]:
    tag_keys = TagService.reorder_tags(tags_keys)
    return [tag_key.to_dto() for tag_key in tag_keys]


@core_app.put("/tag/{key}/{old_value}/{new_value}", tags=["Tag"], summary='Update registered tag value')
def update_registered_tag_value(key: str,
                                old_value: str,
                                new_value: str,
                                _=Depends(AuthService.check_user_access_token)) -> SaveTagModelResonseDTO:
    tag_value_model = TagService.update_registered_tag_value(key, old_value, new_value)
    return SaveTagModelResonseDTO(
        key_model=tag_value_model.tag_key.to_dto(),
        value_model=tag_value_model.to_dto()
    )


@core_app.delete("/tag/{key}/{value}", tags=["Tag"], summary='Delete registered tag')
def delete_registered_tag(key: str,
                          value: str,
                          _=Depends(AuthService.check_user_access_token)) -> None:
    TagService.delete_registered_tag(key, value)

################################# ENTITY TAG #################################


@core_app.get("/tag/entity/{entity_tag_id}", tags=["Tag"], summary='Get 1 tag detail')
def get_tag_detail(entity_tag_id: str,
                   _=Depends(AuthService.check_user_access_token)) -> EntityTagFullDTO:
    return TagService.get_and_check_entity_tag(entity_tag_id).to_full_dto()


@core_app.get("/tag/entity/{entity_type}/{entity_id}", tags=["Tag"], summary='Get tags of an entity')
def get_tags_of_entity(entity_type: EntityType,
                       entity_id: str,
                       _=Depends(AuthService.check_user_access_token)) -> List[EntityTagDTO]:
    return TagService.find_by_entity_id(entity_type, entity_id).to_dto()


@core_app.post(
    "/tag/entity/{entity_type}/{entity_id}/{propagate}", tags=["Tag"],
    summary="Save entity tags")
def add_tag(entity_type: EntityType,
            entity_id: str,
            propagate: bool,
            tags: List[NewTagDTO],
            _=Depends(AuthService.check_user_access_token)) -> List[EntityTagDTO]:
    new_tags = TagService.add_tag_dict_to_entity(entity_type, entity_id, tags, propagate)
    return [tag.to_dto() for tag in new_tags]


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
                               _=Depends(AuthService.check_user_access_token)) -> TagPropagationImpactDTO:
    return TagService.check_propagation_add_tags(entity_type, entity_id, tags)


@core_app.post(
    "/tag/check-propagation-delete/{entity_type}/{entity_id}", tags=["Tag"],
    summary="Check tag propagation impact for tag deletion")
def check_propagation_delete_tag(entity_type: EntityType,
                                 entity_id: str,
                                 tag: NewTagDTO,
                                 _=Depends(AuthService.check_user_access_token)) -> TagPropagationImpactDTO:
    return TagService.check_propagation_delete_tag(entity_type, entity_id, tag)
