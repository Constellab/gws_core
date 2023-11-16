# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.core.exception.exceptions.not_found_exception import \
    NotFoundException
from gws_core.core.model.model import Model
from gws_core.tag.entity_tag import EntityTag, EntityTagType
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import TagDict
from gws_core.tag.tag_helper import TagHelper
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
    def add_tag_to_entity(cls, tag_entity_type: EntityTagType, entity_id: str,
                          tag: Tag) -> EntityTag:

        # add tag to the list of tags
        entity_tags = EntityTagList.find_by_entity(tag_entity_type, entity_id)

        if not tag.origin_is_defined():
            tag.origin_type = TagOriginType.USER
            tag.origin_id = CurrentUserService.get_and_check_current_user().id

        return entity_tags.add_tag_if_not_exist(tag)

    @classmethod
    @transaction()
    def add_tags_to_entity(cls, tag_entity_type: EntityTagType, entity_id: str,
                           tags: List[Tag]) -> EntityTagList:

        entity_tags = EntityTagList.find_by_entity(tag_entity_type, entity_id)

        for tag in tags:
            if not tag.origin_is_defined():
                tag.origin_type = TagOriginType.USER
                tag.origin_id = CurrentUserService.get_and_check_current_user().id

        entity_tags.add_tags_to_entity(tags)

        return entity_tags

    @classmethod
    def add_tags_dict_to_entity(cls, tag_entity_type: EntityTagType, entity_id: str,
                                tags_dict: List[TagDict]) -> EntityTagList:

        tags: List[Tag] = TagHelper.tags_dict_to_list(tags_dict)

        return cls.add_tags_to_entity(tag_entity_type, entity_id, tags)

    @classmethod
    def find_by_entity_id(cls, tag_entity_type: EntityTagType, entity_id: str) -> EntityTagList:
        return EntityTagList.find_by_entity(tag_entity_type, entity_id)

    @classmethod
    def delete_tag_from_entity(cls, tag_entity_type: EntityTagType, entity_id: str,
                               tag_key: str, tag_value: TagValueType) -> None:
        entity_tags = EntityTagList.find_by_entity(tag_entity_type, entity_id)
        entity_tags.delete_tag(Tag(tag_key, tag_value))
