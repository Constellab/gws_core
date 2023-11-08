# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import List, Type

from gws_core.core.exception.exceptions.not_found_exception import \
    NotFoundException
from gws_core.core.model.model import Model
from gws_core.experiment.experiment import Experiment
from gws_core.report.report import Report
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.tag.entity_tag import (EntityTag, EntityTagList,
                                     EntityTagOriginType, EntityTagType)
from gws_core.user.current_user_service import CurrentUserService

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .tag import Tag
from .tag_model import EntityTagValueFormat, TagModel, TagValueType


class TagService():

    @classmethod
    def register_tags(cls, tags: List[Tag]) -> List[TagModel]:
        tag_models: List[TagModel] = []
        for tag in tags:
            tag_models.append(cls.register_tag(tag.key, tag.value))
        return tag_models

    @classmethod
    def register_tag(cls, tag_key: str, tag_value: TagValueType) -> TagModel:
        tag: TagModel = TagModel.find_by_key(tag_key)

        if tag is None:
            value_format: EntityTagValueFormat = EntityTagValueFormat.STRING
            if isinstance(tag_value, int):
                value_format = EntityTagValueFormat.INTEGER
            elif isinstance(tag_value, float):
                value_format = EntityTagValueFormat.FLOAT
            elif isinstance(tag_value, datetime):
                value_format = EntityTagValueFormat.DATETIME
            tag = TagModel.create_tag(tag_key, [tag_value], value_format)
            tag.order = TagModel.get_highest_order() + 1
        else:
            tag.add_value(tag_value)

        return tag.save()

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

        # get all the entity with the old tag to replace with the new one
        EntityTag.delete_tag_value(tag_key, tag_value)

        # update the TagModel
        tag_model.remove_value(tag_value)

        if tag_model.count_values() == 0:
            tag_model.delete_instance()
        else:
            tag_model.save()

    @classmethod
    @transaction()
    def reorder_tags(cls, tag_keys: List[str]) -> List[TagModel]:
        """Update the order of the tags"""

        tag_models: List[TagModel] = cls.get_all_tags()

        result: List[TagModel] = []
        for i, key in enumerate(tag_keys):

            key = Tag.check_parse_tag_str(key)
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

        values = [Tag.check_parse_tag_str(x) for x in values]

        tag_model.set_values(values)
        return tag_model.save()

    ################################# TAGGABLE MODEL #################################

    @classmethod
    @transaction()
    def add_tag_to_entity(cls, model_type: Type[Model], entity_id: str,
                          tag_key: str, tag_value: TagValueType) -> EntityTag:

        tag_entity_type = cls._get_entity_tag_type(model_type)
        # add tag to the list of tags
        TagService.register_tag(tag_key, tag_value)

        entity_tag = EntityTag.create_entity_tag(Tag(tag_key, tag_value), entity_id, tag_entity_type,
                                                 origin_type=EntityTagOriginType.HUMAN,
                                                 origin_id=CurrentUserService.get_and_check_current_user().id)

        return entity_tag

    @classmethod
    @transaction()
    def save_tags_to_entity(cls, model_type: Type[Model], entity_id: str,
                            tags: List[Tag]) -> EntityTagList:

        tag_entity_type = cls._get_entity_tag_type(model_type)

        entity_tags = EntityTagList.find_by_entity(entity_id, tag_entity_type)

        for tag in tags:
            # add tag to the list of tags
            TagService.register_tag(tag.key, tag.value)

            # add tag to entity
            entity_tags.add_tag_if_not_exist(tag,
                                             origin_type=EntityTagOriginType.HUMAN,
                                             origin_id=CurrentUserService.get_and_check_current_user().id)

        return entity_tags

    @classmethod
    def find_by_entity(cls, model: Model) -> EntityTagList:
        return cls.find_by_entity_id(type(model), model.id)

    @classmethod
    def find_by_entity_id(cls, model_type: Type[Model], entity_id: str) -> EntityTagList:
        tag_entity_type = cls._get_entity_tag_type(model_type)
        return EntityTagList.find_by_entity(entity_id, tag_entity_type)

    @classmethod
    def _get_entity_tag_type(cls, entity_type: Type[Model]) -> EntityTagType:
        if entity_type == ResourceModel:
            return EntityTagType.RESOURCE
        elif entity_type == Experiment:
            return EntityTagType.EXPERIMENT
        elif entity_type == ViewConfig:
            return EntityTagType.VIEW
        elif entity_type == Report:
            return EntityTagType.REPORT
        else:
            raise BadRequestException("Can't add tags to this object type")
