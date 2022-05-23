# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from gws_core.core.exception.exceptions.not_found_exception import \
    NotFoundException
from gws_core.core.utils.utils import Utils
from gws_core.experiment.experiment import Experiment
from gws_core.resource.resource_model import ResourceModel

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .tag import Tag, default_tags
from .tag_model import TagModel
from .taggable_model import TaggableModel


class TagService():

    @classmethod
    def init_default_tags(cls) -> None:
        """Create the default tags of the database if not prevent
        """
        if TagModel.select().count() > 0:
            return

        for key, value in default_tags.items():
            TagModel.create(key, value).save()

    @classmethod
    def register_tags(cls, tags: List[Tag]) -> List[TagModel]:
        tag_models: List[TagModel] = []
        for tag in tags:
            tag_models.append(cls.register_tag(tag.key, tag.value))
        return tag_models

    @classmethod
    def register_tag(cls, tag_key: str, tag_value: str) -> TagModel:
        tag: TagModel = TagModel.find_by_key(tag_key)

        if tag is None:
            tag = TagModel.create(tag_key)

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
    def update_registered_tag_value(cls, tag_key: str, old_value: str, new_value: str) -> TagModel:
        """Update a registerer tag value. It update the tag of all entities that use it"""
        tag_model: TagModel = TagModel.find_by_key(tag_key)

        if tag_model is None:
            raise NotFoundException(f"The tag with key '{tag_key}' does not exists")

        if not tag_model.has_value(old_value):
            raise BadRequestException(f"The tag with key '{tag_key}' does not have the value '{old_value}'")

        new_tag = Tag(tag_key, new_value)

        # get all the entity with the old tag to replace with the new one
        old_tag = Tag(tag_key, old_value)
        entities: List[TaggableModel] = cls.get_entities_with_tag([old_tag])

        for entity in entities:
            # replace the tag
            entity.add_or_replace_tag(new_tag.key, new_tag.value)
            entity.save()

        # update the TagModel
        tag_model.update_value(old_value, new_value)
        return tag_model.save()

    @classmethod
    @transaction()
    def delete_registered_tag(cls, tag_key: str, tag_value: str) -> None:
        """Update a registerer tag value. It removes the tag of all entities that use it"""
        tag_model: TagModel = TagModel.find_by_key(tag_key)

        if tag_model is None:
            raise NotFoundException(f"The tag with key '{tag_key}' does not exists")

        if not tag_model.has_value(tag_value):
            raise BadRequestException(f"The tag with key '{tag_key}' does not have the value '{tag_value}'")

        # get all the entity with the old tag to replace with the new one
        tag = Tag(tag_key, tag_value)
        entities: List[TaggableModel] = cls.get_entities_with_tag([tag])

        for entity in entities:
            # replace the tag
            entity.remove_tag(tag_key, tag_value)
            entity.save()

        # update the TagModel
        tag_model.remove_value(tag_value)

        if tag_model.count_values() == 0:
            tag_model.delete_instance()
        else:
            tag_model.save()

    ################################# TAGGABLE MODEL #################################

    @classmethod
    @transaction()
    def add_tag_to_entity(cls, model_type: Type[TaggableModel], id: str,
                          tag_key: str, tag_value: str) -> List[Tag]:

        if not Utils.issubclass(model_type, TaggableModel):
            raise BadRequestException("Can't add tags to this object type")

         # Add tag to resource model
        model: TaggableModel = model_type.get_by_id(id)

        if model is None:
            raise NotFoundException(f"Can't find model with id {id}")

        model.add_or_replace_tag(tag_key, tag_value)
        model.save()

        # add tag to the list of tags
        TagService.register_tag(tag_key, tag_value)

        return model.get_tags()

    @classmethod
    @transaction()
    def save_tags_to_entity(cls, model_type: Type[TaggableModel], id: str,
                            tags: List[Tag]) -> List[Tag]:

        if not Utils.issubclass(model_type, TaggableModel):
            raise BadRequestException("Can't add tags to this object type")

        # Add tag to resource model
        model: TaggableModel = model_type.get_by_id(id)

        if model is None:
            raise NotFoundException(f"Can't find model with id {id}")

        for tag in tags:
            if model.has_tag(tag):
                continue

            # add tag to the list of tags
            TagService.register_tag(tag.key, tag.value)

        # set and save all tags
        model.set_tags(tags)
        model.save()

        return model.get_tags()

    @classmethod
    def get_entities_with_tag(cls, tags: List[Tag]) -> List[TaggableModel]:
        return ResourceModel.find_by_tags(tags) + Experiment.find_by_tags(tags)
