
from typing import List

from peewee import Expression

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..tag.tag import TagHelper
from .resource_model import ResourceModel


class ResourceModelSearchBuilder(SearchBuilder):
    """Search build for the resource model

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ResourceModel, default_order=[ResourceModel.created_at.desc()])

    def get_filter_expression(self, filter: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter['key'] == 'tags':
            return TagHelper.get_search_tag_expression(filter['value'], ResourceModel.tags)

        return super().get_filter_expression(filter)
