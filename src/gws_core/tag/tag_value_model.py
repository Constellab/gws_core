

from datetime import datetime
from typing import Any, Dict

from gws_core.community.community_dto import CommunityTagValueDTO
from gws_core.core.classes.expression_builder import ExpressionBuilder
from gws_core.core.decorator.transaction import transaction
from gws_core.core.model.db_field import JSONField
from gws_core.core.model.model import Model
from gws_core.tag.tag import TagValueType
from gws_core.tag.tag_dto import TagValueFormat, TagValueModelDTO
from gws_core.tag.tag_helper import TagHelper
from gws_core.tag.tag_key_model import TagKeyModel
from peewee import BooleanField, CharField, ForeignKeyField, ModelSelect


class TagValueModel(Model):
    """ Table to store all the existing tag values"""

    _table_name = 'gws_tag_value'

    tag_key: TagKeyModel = ForeignKeyField(TagKeyModel, null=False, index=True,
                                           on_delete='CASCADE', on_update='CASCADE',
                                           field='key', column_name='tag_key')

    tag_value = CharField(null=False)

    is_community_tag_value = BooleanField(default=False)

    short_description = CharField(null=True, default=None)

    additional_infos: Dict[str, Any] = JSONField(null=True)

    deprecated = BooleanField(default=False)

    def get_tag_value(self) -> TagValueType:
        return self.tag_key.convert_str_value_to_type(self.tag_value)

    def get_str_tag_value(self) -> str:
        return self.tag_value

    def to_dto(self) -> TagValueModelDTO:
        return TagValueModelDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            key=self.tag_key.key,
            value=self.get_tag_value(),
            value_format=self.tag_key.value_format,
            is_community_tag_value=self.is_community_tag_value,
            deprecated=self.deprecated,
            short_description=self.short_description,
            additional_infos=self.additional_infos
        )

    @classmethod
    def from_dto(cls, tag_value_model_dto: TagValueModelDTO, tag_key_model: TagKeyModel) -> 'TagValueModel':
        """Update the model from a DTO"""
        tag_value_model = cls()
        tag_value_model.id = tag_value_model_dto.id
        tag_value_model.created_at = tag_value_model_dto.created_at
        tag_value_model.last_modified_at = tag_value_model_dto.last_modified_at
        tag_value_model.tag_key = tag_key_model
        tag_value_model.tag_value = TagHelper.convert_value_to_str(tag_value_model_dto.value)
        tag_value_model.is_community_tag_value = tag_value_model_dto.is_community_tag_value
        tag_value_model.deprecated = tag_value_model_dto.deprecated
        tag_value_model.short_description = tag_value_model_dto.short_description
        tag_value_model.additional_infos = tag_value_model_dto.additional_infos

        return tag_value_model
    ######################################### CLASS METHODS #########################################

    @classmethod
    def tag_value_exists(cls, tag_key: str, tag_value: TagValueType) -> bool:
        """Return true if the tag value exists
        """
        return cls.get_tag_value_model(tag_key, tag_value) is not None

    @classmethod
    @transaction()
    def create_tag_value_if_not_exists(cls, tag_key: str, tag_value: TagValueType) -> 'TagValueModel':
        """Create a tag value model
        """

        # check if the tag value already exists
        tag_value_model = cls.get_tag_value_model(tag_key, tag_value)
        if tag_value_model:
            return tag_value_model

        # cretae the key if it does not exist
        tag_key_model = TagKeyModel.find_by_key(key=tag_key)
        if not tag_key_model:
            value_format: TagValueFormat = TagValueFormat.STRING
            if isinstance(tag_value, int):
                value_format = TagValueFormat.INTEGER
            elif isinstance(tag_value, float):
                value_format = TagValueFormat.FLOAT
            elif isinstance(tag_value, datetime):
                value_format = TagValueFormat.DATETIME
            elif isinstance(tag_value, bool):
                value_format = TagValueFormat.BOOLEAN

            tag_key_model = TagKeyModel.create_tag_key_if_not_exists(tag_key, value_format)

        return cls.create(tag_key=tag_key_model, tag_value=TagHelper.convert_value_to_str(tag_value))

    @classmethod
    @transaction()
    def delete_tag_value(cls, tag_key: str, tag_value: TagValueType) -> None:
        """Delete a tag value model, and the tag key if it has no more values
        """
        tag_value_model = cls.get_tag_value_model(tag_key, tag_value)
        if tag_value_model:
            tag_value_model.delete_instance()

        # check if the tag key has no more values
        tag_key_model = TagValueModel.select().where(TagValueModel.tag_key == tag_key).first()

        if not tag_key_model:
            TagKeyModel.delete_tag(tag_key)

    @classmethod
    def update_tag_value(
            cls, tag_key: str, old_tag_value: TagValueType, new_tag_value: TagValueType) -> 'TagValueModel':
        """Update a tag value model
        """
        tag_value_model = cls.get_tag_value_model(tag_key, old_tag_value)
        if tag_value_model:
            tag_value_model.tag_value = TagHelper.convert_value_to_str(new_tag_value)
            tag_value_model.save()

        return tag_value_model

    ######################################### SELECT #########################################

    @classmethod
    def get_tag_value_model(cls, tag_key: str, tag_value: TagValueType) -> 'TagValueModel':
        """Return the tag value model if it exists
        """
        return cls.get_or_none(tag_key=tag_key, tag_value=TagHelper.convert_value_to_str(tag_value))

    @classmethod
    def find_by_tag_key(cls, tag_key: str) -> ModelSelect:
        return cls.select().where(cls.tag_key == tag_key)

    @classmethod
    def search_by_value(cls, tag_key: str, tag_value: TagValueType = None) -> ModelSelect:
        expression_builder = ExpressionBuilder(cls.tag_key == tag_key)
        if tag_value:
            expression_builder.add_expression(cls.tag_value.contains(TagHelper.convert_value_to_str(tag_value)))
        return cls.select().where(expression_builder.build()).order_by(TagValueModel.tag_value)

    class Meta:
        table_name = 'gws_tag_value'
        indexes = (
            (("tag_key", "tag_value"), True),
        )

    ######################################### COMMUNITY TAG VALUE #########################################

    @classmethod
    def from_community_tag_value(
            cls, community_tag_value: CommunityTagValueDTO, tag_key: TagKeyModel) -> 'TagValueModel':
        """Create a tag value model from a community tag value
        """
        if not community_tag_value:
            return None

        if not tag_key:
            return None

        tag_value_model = cls()
        tag_value_model.id = community_tag_value.id
        tag_value_model.tag_key = tag_key
        tag_value_model.tag_value = community_tag_value.value
        tag_value_model.is_community_tag_value = True
        tag_value_model.short_description = community_tag_value.short_description
        tag_value_model.additional_infos = community_tag_value.additional_infos
        tag_value_model.deprecated = community_tag_value.deprecated

        return tag_value_model
