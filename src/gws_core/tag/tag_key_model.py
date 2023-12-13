# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from peewee import BooleanField, CharField, IntegerField, ModelSelect

from gws_core.core.classes.enum_field import EnumField
from gws_core.tag.tag import TagValueType
from gws_core.tag.tag_dto import EntityTagValueFormat, TagKeyModelDTO
from gws_core.tag.tag_helper import TagHelper

from ..core.model.model import Model


class TagKeyModel(Model):
    key = CharField(null=False, unique=True)
    order = IntegerField(default=0)

    value_format: EntityTagValueFormat = EnumField(
        choices=EntityTagValueFormat, null=False, default=EntityTagValueFormat.STRING)

    is_propagable = BooleanField(default=False)

    _table_name = "gws_tag"

    def convert_str_value_to_type(self, value: str) -> TagValueType:
        return TagHelper.convert_str_value_to_type(value, self.value_format)

    def to_dto(self) -> TagKeyModelDTO:
        return TagKeyModelDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            key=self.key,
            value_format=self.value_format,
            is_propagable=self.is_propagable,
        )

    ############################################## CLASS METHODS ##############################################

    @classmethod
    def create_tag_key_if_not_exists(cls, tag_key: str, value_format: EntityTagValueFormat) -> 'TagKeyModel':
        """Create a tag key model
        """
        tag_key_model = cls.find_by_key(tag_key)
        if tag_key_model:
            return tag_key_model

        tag = TagKeyModel()
        tag.key = tag_key
        tag.value_format = value_format
        tag.order = TagKeyModel.get_highest_order() + 1

        return tag.save()

    @classmethod
    def delete_tag(cls, key: str) -> None:
        tag_model: TagKeyModel = cls.find_by_key(key)

        if tag_model is None:
            return

        tag_model.delete_instance()

    @classmethod
    def find_by_key(cls, key: str) -> Optional['TagKeyModel']:
        try:
            return cls.get(cls.key == key)
        except:
            return None

    @classmethod
    def search_by_key(cls, key: str) -> ModelSelect:
        if key:
            return TagKeyModel.select().where(TagKeyModel.key.contains(key)).order_by(TagKeyModel.key)
        else:
            return TagKeyModel.select().order_by(TagKeyModel.key)

    @classmethod
    def get_highest_order(cls) -> int:
        tag_model: TagKeyModel = cls.select().order_by(cls.order.desc()).first()

        if tag_model:
            return tag_model.order
        return -1

    class Meta:
        table_name = "gws_tag"
