# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from peewee import Expression, Field

from gws_core.tag.entity_tag import EntityTag, EntityTagType
from gws_core.tag.tag_model import EntityTagValueFormat, TagModel

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..tag.tag_helper import TagHelper


class EntityWithTagSearchBuilder(SearchBuilder):
    """Search builder that support search on tags

    :param SearchBuilder: _description_
    :type SearchBuilder: _type_
    """

    entity_type: EntityTagType

    def __init__(self, model_type: Type[EntityTag],
                 entity_type: EntityTagType,
                 default_orders=None) -> None:
        super().__init__(model_type, default_orders=default_orders)
        self.entity_type = entity_type

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_['key'] == 'tags':
            return self.handle_tag_filter(filter_)

        return super().convert_filter_to_expression(filter_)

    def handle_tag_filter(self, filter_: SearchFilterCriteria) -> None:
        """Handle the tag filter
        """
        tags = TagHelper.tags_json_to_list(filter_['value'])

        for tag in tags:
            tag_model: TagModel = TagModel.find_by_key(tag.key)

            if tag_model is None:
                raise Exception(f"Tag with key {tag.key} does not exist")

            entity_alias: Type[EntityTag] = EntityTag.alias()
            tag_value_field = self.get_tag_value_column_filter(entity_alias, tag_model.value_format)
            tag_value = tag_model.check_and_convert_value(tag.value)

            self.add_join(entity_alias, on=((entity_alias.entity_id == self._model_type.id) &
                                            (entity_alias.entity_type == self.entity_type.value) &
                                            (entity_alias.tag_key == tag.key) &
                                            # (tag_value_field == tag_value)
                                            (tag_value_field == tag.value)
                                            ))
        # return none because expression is already added with the join
        return None

    def get_tag_value_column_filter(self, entity_type: Type[EntityTag], value_format: EntityTagValueFormat) -> Field:
        return entity_type.tag_value
        if value_format == EntityTagValueFormat.STRING:
            return entity_type.tag_value
        elif value_format == EntityTagValueFormat.INTEGER:
            return entity_type.tag_value.cast('INTEGER')
        elif value_format == EntityTagValueFormat.FLOAT:
            return entity_type.tag_value.cast('FLOAT')
        elif value_format == EntityTagValueFormat.DATETIME:
            return entity_type.tag_value.cast('DATETIME')
