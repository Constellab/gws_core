# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import Expression

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..tag.tag_helper import TagHelper
from .protocol_template import ProtocolTemplate


class ProtocolTemplateSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(ProtocolTemplate, default_orders=[ProtocolTemplate.last_modified_at.desc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_['key'] == 'tags':
            tags = TagHelper.tags_to_list(filter_['value'])
            return ProtocolTemplate.get_search_tag_expression(tags)

        return super().convert_filter_to_expression(filter_)