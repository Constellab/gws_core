from typing import Optional

from peewee import ModelSelect

from gws_core.community.community_dto import CommunityTagKeyDTO
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.model.typed_db_field import (
    NullableCharField,
    NullableJSONField,
    TypedBooleanField,
    TypedCharField,
    TypedEnumField,
    TypedIntegerField,
)
from gws_core.impl.rich_text.rich_text_db_field import NullableRichTextDbField
from gws_core.tag.tag import Tag, TagValueType
from gws_core.tag.tag_dto import TagKeyModelDTO, TagValueFormat

from ..core.model.model import Model


class TagKeyModel(Model):
    key: TypedCharField = TypedCharField(unique=True)
    order: TypedIntegerField = TypedIntegerField(default=0)

    value_format: TypedEnumField[TagValueFormat] = TypedEnumField(choices=TagValueFormat, default=TagValueFormat.STRING)

    label: NullableCharField = NullableCharField()

    description: NullableRichTextDbField = NullableRichTextDbField()

    is_community_tag: TypedBooleanField = TypedBooleanField(default=False)

    deprecated: TypedBooleanField = TypedBooleanField(default=False)

    additional_infos_specs: NullableJSONField = NullableJSONField()

    def convert_str_value_to_type(self, value: str) -> TagValueType:
        return Tag.convert_value_to_type(value, self.value_format)

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

    def to_community_dto(self) -> CommunityTagKeyDTO:
        """Convert the tag key model to a community tag key DTO"""
        return CommunityTagKeyDTO(
            id=self.id,
            key=self.key,
            label=self.label,
            value_format=self.value_format,
            deprecated=self.deprecated,
            published_at=None,
            unit=None,
            description=self.description,
            created_at=self.created_at.isoformat(),
            last_modified_at=self.last_modified_at.isoformat(),
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
        tag_model = cls.find_by_key(key)

        if tag_model is None:
            return

        tag_model.delete_instance()

    @classmethod
    def find_by_key(cls, key: str) -> Optional["TagKeyModel"]:
        return cls.get_or_none(cls.key == key)

    @classmethod
    def get_by_key(cls, key: str) -> Optional["TagKeyModel"]:
        return cls.select().where(cls.key == key).first()

    @classmethod
    def get_and_check_by_key(cls, key: str) -> "TagKeyModel":
        """Get the tag key model by key and raise an exception if it does not exist"""
        tag_key_model = cls.get_by_key(key)
        if not tag_key_model:
            raise BadRequestException(
                f"The tag key '{key}' does not exists. Please create it first."
            )
        return tag_key_model

    @classmethod
    def search_by_key(cls, key: str) -> ModelSelect:
        return cls.select().where(cls.key.contains(key)).order_by(cls.key)

    @classmethod
    def get_all_ordered_by_key(cls) -> ModelSelect:
        return cls.select().order_by(cls.key)

    @classmethod
    def get_all_ordered_by_order(cls) -> list["TagKeyModel"]:
        """Return all the tag keys ordered by their display order"""
        return list(cls.select().order_by(cls.order))

    @classmethod
    def get_community_tag_keys_imported(cls) -> list["TagKeyModel"]:
        """Get the community tag keys imported"""
        return list(
            cls.select().where(cls.is_community_tag == True).order_by(cls.order)  # noqa: E712
        )

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
