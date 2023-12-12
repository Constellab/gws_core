# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import ModelSelect

from gws_core.core.classes.paginator import Paginator
from gws_core.entity_navigator.entity_navigator import EntityNavigator
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import NewTagDTO, TagPropagationImpactDTO
from gws_core.tag.tag_value_model import TagValueModel
from gws_core.user.current_user_service import CurrentUserService

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .tag import Tag, TagOriginType, TagValueType
from .tag_key_model import TagKeyModel


class TagService():

    @classmethod
    def create_tag(cls, tag_key: str, tag_value: TagValueType) -> TagValueModel:
        return TagValueModel.create_tag_value_if_not_exists(tag_key, tag_value)

    @classmethod
    def get_all_tags(cls) -> List[TagKeyModel]:
        return list(TagKeyModel.select().order_by(TagKeyModel.order))

    @classmethod
    def search_keys(cls,
                    tag_key: str,
                    page: int = 0,
                    number_of_items_per_page: int = 20) -> Paginator[TagKeyModel]:
        model_select: ModelSelect = TagKeyModel.search_by_key(tag_key)

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_values(cls,
                      tag_key: str,
                      tag_value: str,
                      page: int = 0,
                      number_of_items_per_page: int = 20) -> Paginator[TagValueModel]:
        model_select: ModelSelect = TagValueModel.search_by_value(tag_key, tag_value)
        return Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_by_key(cls,
                   tag_key: str) -> TagKeyModel:
        return TagKeyModel.select().where(TagKeyModel.key == tag_key).first()

    @classmethod
    @transaction()
    def update_registered_tag_value(
            cls, tag_key: str, old_value: TagValueType, new_value: TagValueType) -> TagValueModel:
        """Update a registerer tag value. It update the tag of all entities that use it"""

        if not TagValueModel.tag_value_exists(tag_key, old_value):
            raise BadRequestException(
                f"The tag with key '{tag_key}' and value '{old_value}' does not exists")

        # update the TagModel
        return TagValueModel.update_tag_value(tag_key, old_value, new_value)

    @classmethod
    @transaction()
    def delete_registered_tag(cls, tag_key: str, tag_value: TagValueType) -> None:
        """Update a registerer tag value. It removes the tag of all entities that use it"""
        if not TagValueModel.tag_value_exists(tag_key, tag_value):
            raise BadRequestException(
                f"The tag with key '{tag_key}' and value '{tag_value}' does not exists")

        TagValueModel.delete_tag_value(tag_key, tag_value)

    @classmethod
    @transaction()
    def reorder_tags(cls, tag_keys: List[str]) -> List[TagKeyModel]:
        """Update the order of the tags"""

        tag_models: List[TagKeyModel] = cls.get_all_tags()

        result: List[TagKeyModel] = []
        for i, key in enumerate(tag_keys):

            key = Tag.check_parse_tag_key(key)
            tag_model_filtererd: List[TagKeyModel] = [
                x for x in tag_models if x.key == key]

            if len(tag_model_filtererd) == 0:
                continue

            tag_model = tag_model_filtererd[0]
            tag_model.order = i
            tag_model.save()
            result.append(tag_model)

        return result

    ################################# TAGGABLE MODEL #################################

    @classmethod
    @transaction()
    def add_tag_to_entity(cls, entity_type: EntityType, entity_id: str,
                          tag: Tag) -> EntityTag:

        # add tag to the list of tags
        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        if not tag.origin_is_defined():
            tag.origins.add_origin(TagOriginType.USER, CurrentUserService.get_and_check_current_user().id)

        return entity_tags.add_tag(tag)

    @classmethod
    @transaction()
    def add_tags_to_entity(cls, entity_type: EntityType, entity_id: str,
                           tags: List[Tag]) -> List[EntityTag]:

        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        for tag in tags:
            if not tag.origin_is_defined():
                tag.origins.add_origin(TagOriginType.USER, CurrentUserService.get_and_check_current_user().id)

        return entity_tags.add_tags(tags)

    @classmethod
    @transaction()
    def add_tag_dict_to_entity(cls, entity_type: EntityType, entity_id: str,
                               tag_dicts: List[NewTagDTO], propagate: bool) -> List[EntityTag]:

        tags = [Tag(key=tag_dict.key, value=tag_dict.value, is_propagable=propagate) for tag_dict in tag_dicts]

        if propagate:
            return cls.add_tags_to_entity_and_propagate(entity_type, entity_id, tags)
        else:
            return cls.add_tags_to_entity(entity_type, entity_id, tags)

    @classmethod
    @transaction()
    def add_tags_to_entity_and_propagate(cls, entity_type: EntityType, entity_id: str,
                                         tags: List[Tag]) -> List[EntityTag]:
        entity_tags = cls.add_tags_to_entity(entity_type, entity_id, tags)

        # propagate the tag to the next entities
        entity_nav = EntityNavigator.from_entity_id(entity_type, entity_id)
        entity_nav.propagate_tags(tags)

        return entity_tags

    @classmethod
    def find_by_entity_id(cls, entity_type: EntityType, entity_id: str) -> EntityTagList:
        return EntityTagList.find_by_entity(entity_type, entity_id)

    @classmethod
    def delete_tag_from_entity(cls, entity_type: EntityType, entity_id: str,
                               tag_key: str, tag_value: TagValueType) -> None:
        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        tag_to_delete = Tag(tag_key, tag_value)
        current_tag: EntityTag = entity_tags.get_tag(tag_to_delete)

        if not current_tag:
            return

        if not current_tag.origin_is_user():
            raise BadRequestException("You can't delete a tag that is not created by a user")

        current_tag = entity_tags.get_tag(tag_to_delete)

        if current_tag:

            entity_tags.delete_tag(tag_to_delete)

            if current_tag.is_propagable:
                entity_nav = EntityNavigator.from_entity_id(entity_type, entity_id)
                entity_nav.delete_propagated_tags([tag_to_delete])

    @classmethod
    def check_propagation_add_tags(cls, entity_type: EntityType, entity_id: str,
                                   tags: List[NewTagDTO]) -> TagPropagationImpactDTO:
        """Check the impact of the propagation of the given tags
        """
        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        new_tags: List[Tag] = []

        for tag in tags:
            new_tag = Tag(tag.key, tag.value)
            if not entity_tags.has_tag(new_tag):
                new_tags.append(new_tag)

        if len(new_tags) == 0:
            raise BadRequestException("The tags already exists for the object")

        return cls._check_tag_propagation_impact(entity_type, entity_id, new_tags)

    @classmethod
    def check_propagation_delete_tag(cls, entity_type: EntityType, entity_id: str,
                                     tag: NewTagDTO) -> TagPropagationImpactDTO:
        """Check the impact of deletion of a the propagation of the given tags
        """

        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        tag_to_delete = Tag(tag.key, tag.value)

        existing_tag: EntityTag = entity_tags.get_tag(tag_to_delete)

        if not existing_tag:
            raise BadRequestException("The tag does not exists for the object")

        # return only the current entity if the tag is not propagable
        if not existing_tag.is_propagable:
            entity_nav = EntityNavigator.from_entity_id(entity_type, entity_id)
            return TagPropagationImpactDTO(
                tags=[tag_to_delete.to_dto()],
                impacted_entities=entity_nav.get_entities().get_entity_dict_nav_group()
            )

        return cls._check_tag_propagation_impact(entity_type, entity_id, [tag_to_delete])

    @classmethod
    def _check_tag_propagation_impact(cls, entity_type: EntityType, entity_id: str,
                                      tags: List[Tag]) -> TagPropagationImpactDTO:
        """Check the impact of the propagation of the given tags
        """
        entity_nav = EntityNavigator.from_entity_id(entity_type, entity_id)
        # The tags can't be propagated to EXPERIMENT
        next_entities = entity_nav.get_next_entities_recursive(
            [EntityType.RESOURCE, EntityType.VIEW, EntityType.REPORT], include_current_entities=True)

        return TagPropagationImpactDTO(
            tags=[tag.to_dto() for tag in tags],
            impacted_entities=next_entities.get_entity_dict_nav_group()
        )

    @classmethod
    def get_and_check_entity_tag(cls, entity_tag_id: str) -> EntityTag:
        return EntityTag.get_by_id_and_check(entity_tag_id)
