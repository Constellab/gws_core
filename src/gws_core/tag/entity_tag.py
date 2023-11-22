# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import List

from peewee import (BooleanField, CharField, Expression, ForeignKeyField,
                    ModelSelect)

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.classes.expression_builder import ExpressionBuilder
from gws_core.core.model.db_field import JSONField
from gws_core.core.model.model import Model
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.tag import Tag, TagOrigins, TagOriginType, TagValueType
from gws_core.tag.tag_model import TagModel


class EntityTag(Model):
    """ Table to store the tags of all entities"""

    id = CharField(primary_key=True, max_length=36)

    tag_key: TagModel = ForeignKeyField(TagModel, null=False, index=True,
                                        on_delete='CASCADE', on_update='CASCADE',
                                        field='key', column_name='tag_key')

    tag_value = CharField(null=False, index=True)

    # to override in child classes
    entity_id: str = CharField(null=False, max_length=36, index=True)

    entity_type: EntityType = EnumField(choices=EntityType,
                                        null=False, index=True)

    origins = JSONField(null=False)

    is_propagable = BooleanField(default=False)

    # contains the tag key str value
    tag_key_id: str

    _table_name = 'gws_entity_tag'

    def get_tag_key(self) -> str:
        return self.tag_key_id

    def get_tag_value(self) -> TagValueType:
        return self.tag_key.convert_str_value_to_type(self.tag_value)

    def get_str_tag_value(self) -> str:
        return self.tag_value

    def set_value(self, value: TagValueType) -> None:
        checked_value = self.tag_key.check_and_convert_value(value)
        self.tag_value = self.tag_key.convert_value_to_str(checked_value)

    def origin_is_user(self) -> bool:
        return self.get_origins().is_user_origin()

    def get_origins(self) -> TagOrigins:
        return TagOrigins.from_json(self.origins)

    def set_origins(self, origins: TagOrigins) -> None:
        self.origins = origins.to_json()

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        return self.to_simple_tag().to_json()

    def to_simple_tag(self) -> Tag:
        return Tag(key=self.get_tag_key(), value=self.get_tag_value(),
                   is_propagable=self.is_propagable,
                   origins=self.get_origins())

    def merge_tag(self, tag: Tag) -> 'EntityTag':
        """Merge the tag with the current tag. It update the origins and propagable
        """
        origins = self.get_origins()
        tag_updated = origins.merge_origins(tag.origins)

        if not self.is_propagable and tag.is_propagable:
            self.is_propagable = True
            tag_updated = True

        if tag_updated:
            self.set_origins(origins)
            return self.save()
        else:
            return self

    def propagate_tag(self, origin_type: TagOriginType, origin_id: str) -> Tag:
        """Propagate the tag to the entity with the given origin
        """
        return self.to_simple_tag().propagate(origin_type, origin_id)

    ###################################### EDITION ######################################

    @classmethod
    def create_entity_tag(cls, tag: Tag, tag_model: TagModel, entity_id: str,
                          entity_type: EntityType) -> 'EntityTag':
        if not tag.origin_is_defined():
            raise ValueError('The tag origin must be defined to save it')

        if tag.key != tag_model.key:
            raise ValueError('The tag key must be the same as the tag model key')

        entity_tag: EntityTag = EntityTag(
            tag_key=tag_model, entity_id=entity_id, entity_type=entity_type,
            is_propagable=tag.is_propagable,
            origins=tag.origins.to_json())
        entity_tag.set_value(tag.value)
        return entity_tag.save()

    @classmethod
    def update_tag_value(cls, tag_key: str, old_value: str, new_value: str) -> None:
        cls.update(tag_value=new_value).where((cls.tag_key == tag_key) & (cls.tag_value == old_value)).execute()

    @classmethod
    def delete_tag_value(cls, tag_key: str, tag_value: str) -> None:
        cls.delete().where((cls.tag_key == tag_key) & (cls.tag_value == tag_value)).execute()

    @classmethod
    def delete_tag_key(cls, tag_key: str) -> None:
        cls.delete().where(cls.tag_key == tag_key).execute()

    @classmethod
    def delete_by_entity(cls, entity_id: str, entity_type: EntityType) -> None:
        cls.delete().where((cls.entity_id == entity_id) & (cls.entity_type == entity_type.value)).execute()

    ###################################### SELECT ######################################
    @classmethod
    def get_search_tag_expression(cls, tags: List[Tag]) -> Expression:
        """Get the filter expresion for a search in tags column
        """
        query_builder: ExpressionBuilder = ExpressionBuilder()
        for tag in tags:
            if tag.value:
                query_builder.add_expression(
                    (cls.tag_key == tag.key) & (cls.tag_value == tag.value))
            else:
                query_builder.add_expression(cls.tag_key == tag.key)

        return query_builder.build()

    @classmethod
    def find_by_tag_and_entity(cls, tag: Tag, entity_type: EntityType, entity_id: str) -> 'EntityTag':
        return cls.select().where(
            (cls.tag_key == tag.key) &
            (cls.tag_value == tag.value) &
            (cls.entity_type == entity_type.value) &
            (cls.entity_id == entity_id)
        ).first()

    @classmethod
    def find_by_tag_key_and_entity(cls, tag_key: str, entity_type: EntityType, entity_id: str) -> ModelSelect:
        return cls.select().where(
            (cls.tag_key == tag_key) &
            (cls.entity_type == entity_type.value) &
            (cls.entity_id == entity_id)
        )

    @classmethod
    def find_by_entity(cls, entity_type: EntityType, entity_id: str) -> List['EntityTag']:
        return list(cls.select().where(
            (cls.entity_type == entity_type.value) &
            (cls.entity_id == entity_id)
        ))

    @classmethod
    def count_by_tag(cls, tag_key: str, tag_value: str) -> int:
        return cls.select().where(
            (cls.tag_key == tag_key) &
            (cls.tag_value == tag_value)
        ).count()

    @classmethod
    def find_by_entities(cls, entity_type: EntityType, entity_ids: List[str], ) -> List['EntityTag']:
        return list(cls.select().where(
            (cls.entity_type == entity_type.value) &
            (cls.entity_id.in_(entity_ids))
        ))

    class Meta:
        indexes = (
            (("tag_key", "tag_value", "entity_id", "entity_type"), True),
        )
