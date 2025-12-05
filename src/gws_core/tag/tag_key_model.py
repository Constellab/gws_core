from typing import Optional

from peewee import BooleanField, CharField, IntegerField, ModelSelect

from gws_core.community.community_dto import CommunityTagKeyDTO
from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.db_field import JSONField
from gws_core.impl.rich_text.rich_text_db_field import RichTextDbField
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.tag.tag import TagValueType
from gws_core.tag.tag_dto import TagKeyModelDTO, TagValueFormat
from gws_core.tag.tag_helper import TagHelper

from ..core.model.model import Model


class TagKeyModel(Model):
    key = CharField(null=False, unique=True)
    order = IntegerField(default=0)

    value_format: TagValueFormat = EnumField(
        choices=TagValueFormat, null=False, default=TagValueFormat.STRING
    )

    label = CharField(null=True)

    description: RichTextDTO = RichTextDbField(null=True)

    is_community_tag = BooleanField(default=False)

    deprecated = BooleanField(default=False)

    additional_infos_specs: dict = JSONField(null=True)

    def convert_str_value_to_type(self, value: str) -> TagValueType:
        return TagHelper.convert_str_value_to_type(value, self.value_format)

    def to_dto(self) -> TagKeyModelDTO:
        return TagKeyModelDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            key=self.key,
            value_format=self.value_format,
            deprecated=self.deprecated,
            label=self.label,
            description=self.description,
            is_community_tag=self.is_community_tag,
            additional_infos_specs=self.additional_infos_specs,
        )

    ############################################## CLASS METHODS ##############################################

    @classmethod
    def create_tag_key_model(
        cls,
        key: str,
        label: str,
        value_format: TagValueFormat = TagValueFormat.STRING,
        is_community_tag: bool = False,
    ) -> "TagKeyModel":
        return cls.create(
            key=key,
            value_format=value_format,
            label=label,
            is_community_tag=is_community_tag,
            order=cls.get_highest_order() + 1,
        )

    @classmethod
    def delete_tag(cls, key: str) -> None:
        tag_model: TagKeyModel = cls.find_by_key(key)

        if tag_model is None:
            return

        tag_model.delete_instance()

    @classmethod
    def find_by_key(cls, key: str) -> Optional["TagKeyModel"]:
        try:
            return cls.get(cls.key == key)
        except:
            return None

    @classmethod
    def search_by_key(cls, key: str) -> ModelSelect:
        if key:
            return (
                TagKeyModel.select().where(TagKeyModel.key.contains(key)).order_by(TagKeyModel.key)
            )
        else:
            return TagKeyModel.select().order_by(TagKeyModel.key)

    @classmethod
    def get_highest_order(cls) -> int:
        tag_model: TagKeyModel = cls.select().order_by(cls.order.desc()).first()

        if tag_model:
            return tag_model.order
        return -1

    @classmethod
    def from_community_tag_key(
        cls, community_tag_key: CommunityTagKeyDTO, new_only: bool = False
    ) -> Optional["TagKeyModel"]:
        """Create a tag key model from a community tag key"""
        if not community_tag_key:
            return None

        if not new_only:
            tag_key_model = cls.find_by_key(community_tag_key.key)
            if tag_key_model:
                return tag_key_model

        tag = TagKeyModel()
        tag.id = community_tag_key.id
        tag.key = community_tag_key.key
        tag.value_format = community_tag_key.value_format
        tag.label = community_tag_key.label
        tag.description = community_tag_key.description
        tag.deprecated = community_tag_key.deprecated
        tag.is_community_tag = True
        tag.additional_infos_specs = community_tag_key.additional_infos_specs
        tag.order = TagKeyModel.get_highest_order() + 1

        return tag

    class Meta:
        table_name = "gws_tag"
        is_table = True
