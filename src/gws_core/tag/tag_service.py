# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.core.exception.exceptions.not_found_exception import \
    NotFoundException
from gws_core.entity_navigator.entity_navigator import EntityNavigator
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import NewTagDTO, TagPropagationImpactDTO
from gws_core.user.current_user_service import CurrentUserService

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .tag import Tag, TagOriginType, TagValueType
from .tag_model import TagModel


class TagService():

    @classmethod
    def register_tag(cls, tag_key: str, tag_value: TagValueType) -> TagModel:
        return TagModel.register_tag(tag_key, tag_value)

    @classmethod
    def get_all_tags(cls) -> List[TagModel]:
        return list(TagModel.select().order_by(TagModel.order))

    @classmethod
    def search_by_key(cls,
                      tag_key: str) -> List[TagModel]:
        return list(TagModel.select().where(TagModel.key.contains(tag_key)).order_by(TagModel.key))

    @classmethod
    def get_by_key(cls,
                   tag_key: str) -> TagModel:
        return TagModel.select().where(TagModel.key == tag_key).first()

    @classmethod
    @transaction()
    def update_registered_tag_value(cls, tag_key: str, old_value: TagValueType, new_value: TagValueType) -> TagModel:
        """Update a registerer tag value. It update the tag of all entities that use it"""
        tag_model: TagModel = TagModel.find_by_key(tag_key)

        if tag_model is None:
            raise NotFoundException(
                f"The tag with key '{tag_key}' does not exists")

        if not tag_model.has_value(old_value):
            raise BadRequestException(
                f"The tag with key '{tag_key}' does not have the value '{old_value}'")

        # get all the entity with the old tag to replace with the new one
        EntityTag.update_tag_value(tag_key, old_value, new_value)

        # update the TagModel
        tag_model.update_value(old_value, new_value)
        return tag_model.save()

    @classmethod
    @transaction()
    def delete_registered_tag(cls, tag_key: str, tag_value: TagValueType) -> None:
        """Update a registerer tag value. It removes the tag of all entities that use it"""
        tag_model: TagModel = TagModel.find_by_key(tag_key)

        if tag_model is None:
            raise NotFoundException(
                f"The tag with key '{tag_key}' does not exists")

        if not tag_model.has_value(tag_value):
            raise BadRequestException(
                f"The tag with key '{tag_key}' does not have the value '{tag_value}'")

        # delete all this tag in the entity
        EntityTag.delete_tag_value(tag_key, tag_model.convert_value_to_str(tag_value))

        TagModel.delete_tag(tag_key, tag_model.convert_value_to_str(tag_value))

    @classmethod
    @transaction()
    def reorder_tags(cls, tag_keys: List[str]) -> List[TagModel]:
        """Update the order of the tags"""

        tag_models: List[TagModel] = cls.get_all_tags()

        result: List[TagModel] = []
        for i, key in enumerate(tag_keys):

            key = Tag.check_parse_tag_key(key)
            tag_model_filtererd: List[TagModel] = [
                x for x in tag_models if x.key == key]

            if len(tag_model_filtererd) == 0:
                continue

            tag_model = tag_model_filtererd[0]
            tag_model.order = i
            tag_model.save()
            result.append(tag_model)

        return result

    @classmethod
    @transaction()
    def reorder_tag_values(cls, tag_key: str, values: List[str]) -> TagModel:
        """Update the order of the tags"""

        tag_model: TagModel = cls.get_by_key(tag_key)

        if tag_model is None:
            raise NotFoundException(
                f"The tag with key '{tag_key}' does not exists")

        tag_values = [Tag.check_parse_tag_str(x) for x in values]

        tag_model.set_values(tag_values)
        return tag_model.save()

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
                           tags: List[Tag]) -> EntityTagList:

        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        for tag in tags:
            if not tag.origin_is_defined():
                tag.origins.add_origin(TagOriginType.USER, CurrentUserService.get_and_check_current_user().id)

        entity_tags.add_tags(tags)

        return entity_tags

    @classmethod
    @transaction()
    def add_tag_dict_to_entity(cls, entity_type: EntityType, entity_id: str,
                               tag_dicts: List[NewTagDTO], propagate: bool):

        tags = [Tag(key=tag_dict['key'], value=tag_dict['value'], is_propagable=propagate) for tag_dict in tag_dicts]

        if propagate:
            cls.add_tags_to_entity_and_propagate(entity_type, entity_id, tags)
        else:
            cls.add_tags_to_entity(entity_type, entity_id, tags)

        return [tag.to_json() for tag in tags]

    @classmethod
    @transaction()
    def add_tags_to_entity_and_propagate(cls, entity_type: EntityType, entity_id: str,
                                         tags: List[Tag]) -> EntityTagList:
        entity_tag_list = cls.add_tags_to_entity(entity_type, entity_id, tags)

        # propagate the tag to the next entities
        entity_nav = EntityNavigator.from_entity_id(entity_type, entity_id)
        entity_nav.propagate_tags(tags)

        return entity_tag_list

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
            new_tag = Tag(tag['key'], tag['value'])
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

        tag_to_delete = Tag(tag['key'], tag['value'])

        existing_tag: EntityTag = entity_tags.get_tag(tag_to_delete)

        if not existing_tag:
            raise BadRequestException("The tag does not exists for the object")

        # return only the current entity if the tag is not propagable
        if not existing_tag.is_propagable:
            entity_nav = EntityNavigator.from_entity_id(entity_type, entity_id)
            return TagPropagationImpactDTO([tag_to_delete], entity_nav.get_entities().get_entity_dict_nav_group())

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

        return TagPropagationImpactDTO(tags, next_entities.get_entity_dict_nav_group())

    @classmethod
    def get_and_check_entity_tag(cls, entity_tag_id: str) -> EntityTag:
        return EntityTag.get_by_id_and_check(entity_tag_id)
