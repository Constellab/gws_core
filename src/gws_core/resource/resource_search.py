
from typing import List

from peewee import Expression

from ..core.classes.expression_builder import ExpressionBuilder
from ..core.classes.search_builder import SearchBuilder, SearchFilterParam
from ..tag.tag import Tag, TagHelper
from .resource_model import ResourceModel


class ResourceSearchBuilder(SearchBuilder):
    """Search build for the resource model

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ResourceModel, default_order=[ResourceModel.creation_datetime.desc()])

    def get_filter_expression(self, filter: SearchFilterParam) -> Expression:
        # Special case for the tags to filter on all tags
        if filter['field_name'] == 'tags':
            tags: List[Tag] = TagHelper.tags_to_list(filter['value'])
            query_builder: ExpressionBuilder = ExpressionBuilder()
            for tag in tags:
                query_builder.add_expression(ResourceModel.tags.contains(str(tag)))
            return query_builder.build()

        return super().get_filter_expression(filter)
