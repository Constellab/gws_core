
from fastapi.param_functions import Depends

from gws_core.community.community_dto import CommunityGetTagKeysBody
from gws_core.config.param.param_types import ParamSpecSimpleDTO
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.tag.tag_dto import (
    EntityTagDTO,
    EntityTagFullDTO,
    NewTagDTO,
    SaveTagModelResonseDTO,
    ShareTagDTO,
    TagKeyModelCreateDTO,
    TagKeyModelDTO,
    TagOriginDetailDTO,
    TagPropagationImpactDTO,
    TagsNotSynchronizedDTO,
    TagValueEditDTO,
    TagValueModelDTO,
)
from gws_core.tag.tag_entity_type import TagEntityType

from ..core_controller import core_app
from ..user.authorization_service import AuthorizationService
from .tag_service import TagService


#################################### COMMUNITY TAGS ######################################
@core_app.post(
    "/tag/share-tag-to-community/{tag_key}", tags=["Tag"], summary="Share tag to community"
)
def share_tag_to_community(
    tag_key: str, body: ShareTagDTO, _=Depends(AuthorizationService.check_user_access_token)
) -> TagKeyModelDTO:
    """
    Share a tag to the community.
    """
    shared_tag_key = TagService.share_tag_to_community(
        tag_key, body.publish_mode, body.space_selected
    )
    return shared_tag_key.to_dto() if shared_tag_key else None


@core_app.post(
    "/tag/get-community-available-tags", tags=["Tag"], summary="Get community available tags"
)
def get_community_available_tags(
    page: int,
    number_of_items_per_page: int,
    body: CommunityGetTagKeysBody,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[TagKeyModelDTO]:
    """
    Get community available tags
    """
    return TagService.get_community_available_tags(
        body.spacesFilter, body.labelFilter, body.personalOnly, page, number_of_items_per_page
    )


@core_app.get(
    "/tag/get-community-tag-values/{tag_key}", tags=["Tag"], summary="Get community tag values"
)
def get_community_tag_values(
    tag_key: str,
    page: int,
    number_of_items_per_page: int,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[TagValueModelDTO]:
    """
    Get community tag key values
    """
    return TagService.get_community_tag_values(tag_key, page, number_of_items_per_page)


@core_app.get(
    "/tag/community/get-not-synchronized-community-tags",
    tags=["Tag"],
    summary="Get not synchronized community tags",
)
def get_not_synchronized_community_tags(
    _=Depends(AuthorizationService.check_user_access_token),
) -> TagsNotSynchronizedDTO:
    """
    Get not synchronized community tags
    """
    return TagService.get_not_synchronized_community_tags()


@core_app.post(
    "/tag/community/synchronize-community-tags", tags=["Tag"], summary="Synchronize community tags"
)
def synchronize_community_tags(
    tags_not_sync: TagsNotSynchronizedDTO, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    """
    Synchronize community tags
    """
    TagService.apply_sync(tags_not_sync)


#################################### TAG ####################################


@core_app.post("/tag/key", tags=["Tag"], summary="Create tag key")
def create_tag_key(
    tag_key_dto: TagKeyModelCreateDTO, _=Depends(AuthorizationService.check_user_access_token)
) -> TagKeyModelDTO:
    """
    Create a new tag key.
    """
    tag_key_model = TagService.create_tag_key(tag_key_dto.key, tag_key_dto.label)
    return tag_key_model.to_dto()


@core_app.post("/tag/search", tags=["Tag"], summary="Advanced search for tags")
def advanced_search(
    search_dict: SearchParams,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[TagKeyModelDTO]:
    """
    Advanced search on tags
    """

    return TagService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/tag/search/key", tags=["Tag"], summary="Search tags by key")
def search_all_keys(
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> PageDTO[TagKeyModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_keys(None, page, number_of_items_per_page)


@core_app.get("/tag/search/key/{key}", tags=["Tag"], summary="Search tags by key")
def search_keys(
    key: str | None,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> PageDTO[TagKeyModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_keys(key, page, number_of_items_per_page)


@core_app.get("/tag/search/key/{key}/value", tags=["Tag"], summary="Search tags by value")
def search_all_values(
    key: str,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> PageDTO[TagValueModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_values(key, None, page, number_of_items_per_page).to_dto()


@core_app.get("/tag/search/key/{key}/value/{value}", tags=["Tag"], summary="Search tags by value")
def search_values(
    key: str,
    value: str | None,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> PageDTO[TagValueModelDTO]:
    """
    Search tags by key.
    """

    return TagService.search_values(key, value, page, number_of_items_per_page).to_dto()


@core_app.post(
    "/tag/{key}/additional-info-spec/{spec_name}",
    tags=["Tag"],
    summary="Add additional info spec to tag key",
)
def add_additional_info_spec_to_tag_key(
    key: str,
    spec_name: str,
    spec: ParamSpecSimpleDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> dict[str, ParamSpecSimpleDTO]:
    """
    Add additional info spec to tag key.
    """
    return TagService.add_additional_info_spec_to_tag_key(key, spec_name, spec)


@core_app.put("/tag/{key}/label", tags=["Tag"], summary="Update label of tag key")
def update_tag_key_label(
    key: str, body: TagKeyModelCreateDTO, _=Depends(AuthorizationService.check_user_access_token)
) -> TagKeyModelDTO:
    """
    Update label of tag key.
    """
    tag_key_model = TagService.update_tag_key_label(key, body.label)
    return tag_key_model.to_dto()


@core_app.put(
    "/tag/{key}/additional-info-spec/{spec_name}",
    tags=["Tag"],
    summary="Update additional info spec of tag key",
)
def update_additional_info_spec_to_tag_key(
    key: str,
    spec_name: str,
    spec: ParamSpecSimpleDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> dict[str, ParamSpecSimpleDTO]:
    """
    Update additional info spec of tag key.
    """
    return TagService.update_additional_info_spec_to_tag_key(key, spec_name, spec)


@core_app.put(
    "/tag/{key}/additional-info-spec/{old_spec_name}/{new_spec_name}",
    tags=["Tag"],
    summary="Rename additional info spec of tag key",
)
def rename_and_update_additional_info_spec_to_tag_key(
    key: str,
    old_spec_name: str,
    new_spec_name: str,
    spec: ParamSpecSimpleDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> dict[str, ParamSpecSimpleDTO]:
    """
    Rename additional info spec of tag key.
    """
    return TagService.rename_and_update_additional_info_spec_to_tag_key(
        key, old_spec_name, new_spec_name, spec
    )


@core_app.delete(
    "/tag/{key}/additional-info-spec/{spec_name}",
    tags=["Tag"],
    summary="Delete additional info spec of tag key",
)
def delete_additional_info_spec_to_tag_key(
    key: str, spec_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> dict[str, ParamSpecSimpleDTO]:
    """
    Delete additional info spec of tag key.
    """
    return TagService.delete_additional_info_spec_to_tag_key(key, spec_name)


@core_app.post("/tag/{key}/create-value", tags=["Tag"], summary="Create tag value")
def create_tag_value(
    key: str,
    tag_value_dto: TagValueEditDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TagValueModelDTO:
    """
    Create a new tag value for the given tag key.
    """
    tag_value_model = TagService.create_tag_value(tag_value_dto)
    return tag_value_model.to_dto()


@core_app.post("/tag/{key}/get-value", tags=["Tag"], summary="Get tag value by key and value")
def get_tag_value_by_key_and_value(
    key: str,
    tag_value_dto: TagValueEditDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TagValueModelDTO:
    """
    Get tag value by key and value.
    """
    tag_value_model = TagService.get_tag_value_by_key_and_value(key, tag_value_dto.value)
    return tag_value_model.to_dto() if tag_value_model else None


@core_app.put("/tag/{key}/update-value", tags=["Tag"], summary="Update tag value")
def update_tag_value(
    key: str,
    tag_value_edit_dto: TagValueEditDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> SaveTagModelResonseDTO:
    tag_value_model = TagService.update_tag_value(key, tag_value_edit_dto)
    return SaveTagModelResonseDTO(
        key_model=tag_value_model.tag_key.to_dto(), value_model=tag_value_model.to_dto()
    )


@core_app.put("/tag/reorder", tags=["Tag"], summary="Reoarder tags")
def reorder_tags(
    tags_keys: list[str], _=Depends(AuthorizationService.check_user_access_token)
) -> list[TagKeyModelDTO]:
    tag_keys = TagService.reorder_tags(tags_keys)
    return [tag_key.to_dto() for tag_key in tag_keys]


@core_app.put(
    "/tag/{key}/{old_value}/{new_value}", tags=["Tag"], summary="Update registered tag value"
)
def update_registered_tag_value(
    key: str,
    old_value: str,
    new_value: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> SaveTagModelResonseDTO:
    tag_value_model = TagService.update_registered_tag_value(key, old_value, new_value)
    return SaveTagModelResonseDTO(
        key_model=tag_value_model.tag_key.to_dto(), value_model=tag_value_model.to_dto()
    )


@core_app.delete("/tag/value/{tag_value_id}", tags=["Tag"], summary="Delete tag value")
def delete_tag_value(
    tag_value_id: str, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    """
    Delete tag value by key and value.
    """
    TagService.delete_tag_value(tag_value_id)


@core_app.delete("/tag/{key}", tags=["Tag"], summary="Delete tag key")
def delete_tag_key(key: str, _=Depends(AuthorizationService.check_user_access_token)) -> None:
    """
    Delete tag key by key.
    """
    TagService.delete_tag_key(key)


@core_app.delete("/tag/{key}/{value}", tags=["Tag"], summary="Delete registered tag")
def delete_registered_tag(
    key: str, value: str, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    TagService.delete_registered_tag(key, value)


@core_app.get("/tag/{key}", tags=["Tag"], summary="Get tag by key")
def get_tag_key_by_key(
    key: str, _=Depends(AuthorizationService.check_user_access_token)
) -> TagKeyModelDTO:
    """
    Get tag by key
    """
    tag_key = TagService.get_by_key(key)
    return tag_key.to_dto() if tag_key else None


################################# ENTITY TAG #################################


@core_app.get(
    "/tag/entity/{entity_tag_id}", tags=["Tag"], summary="Get detail info of an entity tag"
)
def get_tag_detail(
    entity_tag_id: str, _=Depends(AuthorizationService.check_user_access_token)
) -> EntityTagFullDTO:
    return TagService.get_and_check_entity_tag(entity_tag_id).to_full_dto()


@core_app.get("/tag/entity/{entity_tag_id}/origins", tags=["Tag"], summary="Get origins of a tag")
def get_tag_origins(
    entity_tag_id: str, _=Depends(AuthorizationService.check_user_access_token)
) -> list[TagOriginDetailDTO]:
    return TagService.get_tag_origins(entity_tag_id)


@core_app.get(
    "/tag/entity/{entity_type}/{entity_id}", tags=["Tag"], summary="Get tags of an entity"
)
def get_tags_of_entity(
    entity_type: TagEntityType,
    entity_id: str,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> list[EntityTagDTO]:
    return TagService.find_by_entity_id(entity_type, entity_id).to_dto()


@core_app.post(
    "/tag/entity/{entity_type}/{entity_id}/{propagate}", tags=["Tag"], summary="Save entity tags"
)
def add_tag(
    entity_type: TagEntityType,
    entity_id: str,
    propagate: bool,
    tags: list[NewTagDTO],
    _=Depends(AuthorizationService.check_user_access_token),
) -> list[EntityTagDTO]:
    new_tags = TagService.add_tag_dict_to_entity(entity_type, entity_id, tags, propagate)
    return [tag.to_dto() for tag in new_tags]


@core_app.delete(
    "/tag/entity/{entity_type}/{entity_id}/{tag_key}/{tag_value}",
    tags=["Tag"],
    summary="Delete entity tag",
)
def delete_tag(
    entity_type: TagEntityType,
    entity_id: str,
    tag_key: str,
    tag_value: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> None:
    TagService.delete_tag_from_entity(entity_type, entity_id, tag_key, tag_value)


################################### CHECK PROPAGATION ####################################
@core_app.post(
    "/tag/check-propagation-add/{entity_type}/{entity_id}",
    tags=["Tag"],
    summary="Check tag propagation impact for tags addition",
)
def check_propagation_add_tags(
    entity_type: TagEntityType,
    entity_id: str,
    tags: list[NewTagDTO],
    _=Depends(AuthorizationService.check_user_access_token),
) -> TagPropagationImpactDTO:
    return TagService.check_propagation_add_tags(entity_type, entity_id, tags)


@core_app.post(
    "/tag/check-propagation-delete/{entity_type}/{entity_id}",
    tags=["Tag"],
    summary="Check tag propagation impact for tag deletion",
)
def check_propagation_delete_tag(
    entity_type: TagEntityType,
    entity_id: str,
    tag: NewTagDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TagPropagationImpactDTO:
    return TagService.check_propagation_delete_tag(entity_type, entity_id, tag)
