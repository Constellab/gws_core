

from peewee import Expression
from playhouse.mysql_ext import Match

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..model.typing import Typing


class TypingSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Typing, default_order=[Typing.human_name.asc()])

    def get_filter_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_['key'] == 'text':
            # on text key, full text search on title and description
            return Match(
                (Typing.human_name, Typing.short_description, Typing.model_name),
                filter_['value'],
                modifier='IN BOOLEAN MODE')

        return super().get_filter_expression(filter_)
