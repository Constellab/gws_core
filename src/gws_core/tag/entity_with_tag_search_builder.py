

from typing import Type

from gws_core.core.model.model import Model
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import Tag
from gws_core.tag.tag_dto import EntityTagValueFormat
from gws_core.tag.tag_key_model import TagKeyModel
from peewee import Expression, Field

from ..core.classes.search_builder import (SearchBuilder, SearchFilterCriteria,
                                           SearchOperator)
from ..tag.tag_helper import TagHelper


class EntityWithTagSearchBuilder(SearchBuilder):
    """Search builder that support search on tags

    :param SearchBuilder: _description_
    :type SearchBuilder: _type_
    """

    entity_type: EntityType

    def __init__(self, model_type: Type[Model],
                 entity_type: EntityType,
                 default_orders=None) -> None:
        super().__init__(model_type, default_orders=default_orders)
        self.entity_type = entity_type

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_.key == 'tags':
            return self.handle_tag_filter(filter_)

        return super().convert_filter_to_expression(filter_)

    def handle_tag_filter(self, filter_: SearchFilterCriteria) -> Expression:
        """Handle the tag filter
        """
        tags = TagHelper.tags_dict_to_list(filter_.value)

        for tag in tags:
            self.add_tag_filter(tag, filter_.operator)

        # return none because expression is already added with the join
        return None

    def add_tag_filter(self, tag: Tag, value_operator: SearchOperator = SearchOperator.EQ,
                       error_if_key_not_exists: bool = False) -> None:

        if error_if_key_not_exists:
            tag_model: TagKeyModel = TagKeyModel.find_by_key(tag.key)

            if tag_model is None:
                raise Exception(f"Tag with key {tag.key} does not exist")

        entity_alias: Type[EntityTag] = EntityTag.alias()
        # tag_value_field = self.get_tag_value_column_filter(entity_alias, tag_model.value_format)
        # TODO add support for CAST for Greater than integer for example

        self.add_join(entity_alias, on=((entity_alias.entity_id == self._model_type.id) &
                                        (entity_alias.entity_type == self.entity_type.value) &
                                        (entity_alias.tag_key == tag.key) &
                                        # (tag_value_field == tag_value)
                                        # (tag_value_field.contains(tag.value)) &
                                        (self._get_expression(value_operator, entity_alias.tag_value, tag.value))
                                        ))

    def get_tag_value_column_filter(self, entity_type: Type[EntityTag], value_format: EntityTagValueFormat) -> Field:
        return entity_type.tag_value
        # if value_format == EntityTagValueFormat.STRING:
        #     return entity_type.tag_value
        # elif value_format == EntityTagValueFormat.INTEGER:
        #     return entity_type.tag_value.cast('INTEGER')
        # elif value_format == EntityTagValueFormat.FLOAT:
        #     return entity_type.tag_value.cast('FLOAT')
        # elif value_format == EntityTagValueFormat.DATETIME:
        #     return entity_type.tag_value.cast('DATETIME')
