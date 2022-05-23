# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import Expression

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..tag.tag_helper import TagHelper
from .resource_model import ResourceModel


class ResourceModelSearchBuilder(SearchBuilder):
    """Search build for the resource model

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ResourceModel, default_orders=[ResourceModel.created_at.desc()])

    def convert_filter_to_expression(self, filter: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter['key'] == 'tags':
            tags = TagHelper.tags_to_list(filter['value'])
            return ResourceModel.get_search_tag_expression(tags)

        return super().convert_filter_to_expression(filter)
