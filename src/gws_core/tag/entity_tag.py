# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import List, Optional

from peewee import CharField, Expression, ForeignKeyField

from gws_core.core.classes.enum_field import IntEnumField
from gws_core.core.classes.expression_builder import ExpressionBuilder
from gws_core.core.model.model import Model
from gws_core.tag.tag import Tag
from gws_core.tag.tag_model import TagModel, TagValueType


class EntityTagType(Enum):
    EXPERIMENT = 0
    RESOURCE = 1
    REPORT = 2
    VIEW = 3


class EntityTagOriginType(Enum):
    HUMAN = 0
    MACHINE = 1


class EntityTag(Model):
    """ Table to store the tags of all entities"""

    id = CharField(primary_key=True, max_length=36)

    tag_key: TagModel = ForeignKeyField(TagModel, lazy_load=True, null=False, index=True,
                                        on_delete='CASCADE', on_update='CASCADE',
                                        field='key', column_name='tag_key')

    tag_value = CharField(null=False, index=True)

    # to override in child classes
    entity_id: str = CharField(null=False, max_length=36, index=True)

    entity_type: EntityTagType = IntEnumField(choices=EntityTagType,
                                              null=False, index=True)

    origin_type: EntityTagOriginType = IntEnumField(choices=EntityTagOriginType, null=False)

    origin_id: str = CharField(null=False, max_length=36)

    # contains the tag key str value
    tag_key_id: str

    _table_name = 'gws_entity_tag'

    def get_tag_key(self) -> str:
        return self.tag_key_id

    def get_value(self) -> TagValueType:
        return self.tag_key.convert_str_value_to_type(self.tag_value)

    def set_value(self, value: TagValueType) -> None:
        checked_value = self.tag_key.check_and_convert_value(value)
        self.tag_value = self.tag_key.convert_value_to_str(checked_value)

    @classmethod
    def create_entity_tag(cls, tag: Tag, entity_id: str, entity_type: EntityTagType,
                          origin_type: EntityTagOriginType, origin_id: str) -> 'EntityTag':
        entity_tag: EntityTag = EntityTag(
            tag_key=tag.key, entity_id=entity_id, entity_type=entity_type.value,
            origin_type=origin_type.value, origin_id=origin_id)
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
    def find_by_tag_and_entity(cls, tag: Tag, entity_id: str, entity_type: EntityTagType) -> 'EntityTag':
        return cls.select().where(
            (cls.tag_key == tag.key) &
            (cls.tag_value == tag.value) &
            (cls.entity_id == entity_id) &
            (cls.entity_type == entity_type.value)
        ).first()

    @classmethod
    def find_by_entity(cls, entity_id: str, entity_type: EntityTagType) -> List['EntityTag']:
        return list(cls.select().where(
            (cls.entity_id == entity_id) &
            (cls.entity_type == entity_type.value)
        ))

    class Meta:
        indexes = (
            (("tag_key", "tag_value", "entity_id", "entity_type"), True),
        )


class EntityTagList():
    """Aggregate to manager tags of an entity
    """

    _entity_id: str
    _entity_type: EntityTagType

    _tags: List[EntityTag]

    def __init__(self, entity_id: str, entity_type: EntityTagType, tags: List[EntityTag]) -> None:
        self._entity_id = entity_id
        self._entity_type = entity_type
        self._tags = tags

    def has_tag(self, tag: Tag) -> bool:
        """return true if the tag key and value already exist in the model
        """
        return self.get_tag(tag) is not None

    def get_tag(self, tag: Tag) -> Optional[EntityTag]:
        """return the tag if it exists
        """
        tags = [entity_tag for entity_tag in self._tags if entity_tag.get_tag_key() ==
                tag.key and entity_tag.get_value() == tag.value]

        if len(tags) > 0:
            return tags[0]

        return None

    def get_tags(self) -> List[EntityTag]:
        return self._tags

    def add_tag_if_not_exist(self, tag: Tag, origin_type: EntityTagOriginType, origin_id: str) -> EntityTag:
        """Add a tag to the list if it does not exist
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is not None:
            return existing_tag

        new_tag = EntityTag.create_entity_tag(tag, self._entity_id, self._entity_type,
                                              origin_type=origin_type, origin_id=origin_id)
        self._tags.append(new_tag)
        return new_tag

    #################################### CLASS METHODS ####################################

    @classmethod
    def find_by_entity(cls, entity_id: str, entity_type: EntityTagType) -> 'EntityTagList':
        return EntityTagList(entity_id, entity_type, EntityTag.find_by_entity(entity_id, entity_type))
