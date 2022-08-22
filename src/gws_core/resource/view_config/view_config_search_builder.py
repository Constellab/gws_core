# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ast import Expression

from gws_core.tag.tag_helper import TagHelper

from ...core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from .view_config import ViewConfig


class ViewConfigSearchBuilder(SearchBuilder):
    """Search build for the view cofnig

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ViewConfig, default_orders=[ViewConfig.last_modified_at.desc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_['key'] == 'tags':
            tags = TagHelper.tags_to_list(filter_['value'])
            return ViewConfig.get_search_tag_expression(tags)

        return super().convert_filter_to_expression(filter_)
