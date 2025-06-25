from typing import Type

from peewee import Expression, Field

from gws_core.core.model.model import Model
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import Tag
from gws_core.tag.tag_dto import TagValueFormat
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_key_model import TagKeyModel

from ..core.classes.search_builder import (SearchBuilder, SearchBuilderType,
                                           SearchFilterCriteria,
                                           SearchOperator)


class EntityWithTagSearchBuilder(SearchBuilder):
    """Search builder that support search on tags

    :param SearchBuilder: _description_
    :type SearchBuilder: _type_
    """

    entity_type: TagEntityType = None

    def __init__(self, model_type: Type[Model],
                 entity_type: TagEntityType,
                 default_orders=None) -> None:
        super().__init__(model_type, default_orders=default_orders)
        self.entity_type = entity_type

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_.key == 'tags':
            return self._handle_tag_filter(filter_)

        return super().convert_filter_to_expression(filter_)

    def _handle_tag_filter(self, filter_: SearchFilterCriteria) -> Expression:
        """Handle the tag filter
        """
        tags = [Tag(tag_dict['key'], tag_dict['value']) if 'value' in tag_dict else Tag(tag_dict['key'], None)
                for tag_dict in filter_.value]

        for tag in tags:
            self.add_tag_filter(tag, filter_.operator if tag.value is not None else SearchOperator.NOT_NULL)

        # return none because expression is already added with the join
        return None

    def add_tag_filter(self, tag: Tag, value_operator: SearchOperator = SearchOperator.EQ,
                       error_if_key_not_exists: bool = False) -> SearchBuilderType:

        # value_format: TagValueFormat = tag.get_value_format()
        if error_if_key_not_exists:
            tag_model: TagKeyModel = TagKeyModel.find_by_key(tag.key)

            if tag_model is None:
                raise Exception(f"Tag with key {tag.key} does not exist")

            # value_format = tag_model.value_format

        entity_alias: Type[EntityTag] = EntityTag.alias()
        # TODO add support for CAST for Greater than integer for example
        # tag_value_field = self._get_tag_value_column_filter(entity_alias, value_format)

        self.add_join(entity_alias, on=((entity_alias.entity_id == self._model_type.id) &
                                        (entity_alias.entity_type == self.entity_type.value) &
                                        (entity_alias.tag_key == tag.key) &
                                        # (tag_value_field == tag_value)
                                        # (tag_value_field.contains(tag.value)) &
                                        (self._get_expression(value_operator, entity_alias.tag_value, tag.get_str_value()))
                                        ))

        return self

    def add_tag_key_filter(self, tag_key: str) -> SearchBuilderType:
        """Add a tag key filter to the search builder
        """
        entity_alias: Type[EntityTag] = EntityTag.alias()
        self.add_join(entity_alias, on=((entity_alias.entity_id == self._model_type.id) &
                                        (entity_alias.entity_type == self.entity_type.value) &
                                        (entity_alias.tag_key == tag_key)))

        return self

    def _get_tag_value_column_filter(self, entity_type: Type[EntityTag], value_format: TagValueFormat) -> Field:
        # return entity_type.tag_value
        if value_format == TagValueFormat.STRING:
            return entity_type.tag_value
        elif value_format == TagValueFormat.INTEGER:
            return entity_type.tag_value.cast('INTEGER')
        elif value_format == TagValueFormat.FLOAT:
            return entity_type.tag_value.cast('FLOAT')
        elif value_format == TagValueFormat.DATETIME:
            return entity_type.tag_value.cast('DATETIME')
