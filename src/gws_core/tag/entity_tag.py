

from typing import List

from peewee import BooleanField, CharField, Expression, ModelSelect

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.classes.expression_builder import ExpressionBuilder
from gws_core.core.model.db_field import JSONField
from gws_core.core.model.model import Model
from gws_core.tag.tag import Tag, TagOrigins, TagValueType
from gws_core.tag.tag_dto import (EntityTagDTO, EntityTagFullDTO, TagOriginDTO,
                                  TagOriginType, TagValueFormat)
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_helper import TagHelper
from gws_core.tag.tag_key_model import TagKeyModel


class EntityTag(Model):
    """ Table to store the tags of all entities"""

    tag_key = CharField(null=False)

    # use utf8mb4_bin collation to ensure case-sensitive comparison
    tag_value = CharField(null=False, collation='utf8mb4_bin')

    value_format: TagValueFormat = EnumField(
        choices=TagValueFormat, null=False, default=TagValueFormat.STRING)

    # to override in child classes
    entity_id: str = CharField(null=False, max_length=36)

    entity_type: TagEntityType = EnumField(choices=TagEntityType,
                                           null=False)

    origins = JSONField(null=False)

    is_propagable = BooleanField(default=False)

    _table_name = 'gws_entity_tag'

    def get_tag_value(self) -> TagValueType:
        return TagHelper.convert_str_value_to_type(self.tag_value, self.value_format)

    def set_value(self, value: TagValueType) -> None:
        checked_value = TagHelper.check_and_convert_value(
            value, self.value_format)
        self.tag_value = TagHelper.convert_value_to_str(checked_value)

    def origin_is_user(self) -> bool:
        return self.get_origins().is_user_origin()

    def get_origins(self) -> TagOrigins:
        return TagOrigins.from_dto(TagOriginDTO.from_json_list(self.origins))

    def set_origins(self, origins: TagOrigins) -> None:
        self.origins = origins.to_json()

    def to_dto(self) -> EntityTagDTO:
        tag_key_model = self.get_tag_key_model()
        return EntityTagDTO(
            id=self.id,
            key=self.tag_key,
            value=self.get_tag_value(),
            is_user_origin=self.origin_is_user(),
            label=tag_key_model.label,
            is_community_tag_key=tag_key_model.is_community_tag
        )

    def to_full_dto(self) -> EntityTagFullDTO:
        tag_key_model = self.get_tag_key_model()
        return EntityTagFullDTO(
            id=self.id,
            key=self.tag_key,
            value=self.get_tag_value(),
            is_user_origin=self.origin_is_user(),
            label=tag_key_model.label,
            is_community_tag_key=tag_key_model.is_community_tag,
            is_propagable=self.is_propagable,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
        )

    def to_simple_tag(self) -> Tag:
        return Tag(key=self.tag_key, value=self.get_tag_value(),
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

    def get_tag_key_model(self) -> TagKeyModel:
        """Get the label of the tag key
        """
        tag_key_model = TagKeyModel.find_by_key(self.tag_key)
        if not tag_key_model:
            raise ValueError(f'Tag key {self.tag_key} not found in tag keys')
        return tag_key_model

    ###################################### EDITION ######################################

    @classmethod
    def create_entity_tag(cls, key: str, value: TagValueType,
                          is_propagable: bool, origins: TagOrigins,
                          value_format: TagValueFormat, entity_id: str,
                          entity_type: TagEntityType, label: str = None,
                          is_community_tag: bool = False) -> 'EntityTag':
        if not origins or origins.is_empty():
            raise ValueError('The tag origin must be defined to save it')

        entity_tag: EntityTag = EntityTag(
            tag_key=key, value_format=value_format,
            entity_id=entity_id, entity_type=entity_type,
            is_propagable=is_propagable,
            is_community_tag=is_community_tag,
            tag_key_label=label
        )
        entity_tag.set_value(value)
        entity_tag.set_origins(origins)
        return entity_tag.save()

    @classmethod
    def delete_by_entity(cls, entity_id: str, entity_type: TagEntityType) -> None:
        cls.delete().where((cls.entity_id == entity_id) & (
            cls.entity_type == entity_type.value)).execute()

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
    def find_by_tag_and_entity(cls, tag: Tag, entity_type: TagEntityType, entity_id: str) -> 'EntityTag':
        return cls.select().where(
            (cls.tag_key == tag.key) &
            (cls.tag_value == tag.value) &
            (cls.entity_type == entity_type.value) &
            (cls.entity_id == entity_id)
        ).first()

    @classmethod
    def find_by_tag_key_and_entity(cls, tag_key: str, entity_type: TagEntityType, entity_id: str) -> ModelSelect:
        return cls.select().where(
            (cls.tag_key == tag_key) &
            (cls.entity_type == entity_type.value) &
            (cls.entity_id == entity_id)
        )

    @classmethod
    def find_by_entity(cls, entity_type: TagEntityType, entity_id: str) -> List['EntityTag']:
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
    def find_by_entities(cls, entity_type: TagEntityType, entity_ids: List[str]) -> List['EntityTag']:
        return list(cls.select().where(
            (cls.entity_type == entity_type.value) &
            (cls.entity_id.in_(entity_ids))
        ))

    @classmethod
    def find_by_entity_type_and_tag(cls, entity_type: TagEntityType, tag: Tag) -> ModelSelect:
        return cls.select().where(
            (cls.entity_type == entity_type.value) &
            (cls.tag_key == tag.key) &
            (cls.tag_value == tag.value)
        )

    @classmethod
    def after_all_tables_init(cls):
        # check if a foreign key exist on column tag_key
        if not cls.foreign_key_exists('tag_key'):

            # create the foreign key on tag_key and tag_value manually after every tables are created
            # because it only works when table gws_tag_value is fully ready
            cls.get_db_manager().db.execute_sql(
                f"alter table {cls.get_table_name()} add constraint entity_tag_foreign_key_value foreign key (tag_key, tag_value) references gws_tag_value (tag_key, tag_value) on delete cascade on update cascade")

    class Meta:
        table_name = 'gws_entity_tag'
        indexes = (
            (("tag_key", "tag_value"), False),
            (("entity_id", "entity_type"), False),
            (("tag_key", "tag_value", "entity_id", "entity_type"), True),
        )
