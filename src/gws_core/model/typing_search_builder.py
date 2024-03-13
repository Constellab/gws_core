

from typing import Type

from peewee import Expression

from ..core.classes.search_builder import SearchBuilder, SearchFilterCriteria
from ..model.typing import Typing


class TypingSearchBuilder(SearchBuilder):

    _model_type: Type[Typing]

    def __init__(self, type_: Type[Typing] = Typing) -> None:
        super().__init__(type_, default_orders=[type_.human_name.asc()])

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        # Special case for the tags to filter on all tags
        if filter_['key'] == 'text':
            # on text key, full text search on title and description
            # return Match(
            #     (self._model_type.human_name, self._model_type.short_description, self._model_type.unique_name),
            #     filter_['value'],
            #     modifier='IN BOOLEAN MODE')
            # contains  on human_name short_description or unique_name
            return (self._model_type.human_name.contains(filter_['value']) | self._model_type.short_description.contains(
                filter_['value']) | self._model_type.unique_name.contains(filter_['value']))

        elif filter_['key'] == 'include_deprecated':
            if not filter_['value']:
                return self._model_type.deprecated_since.is_null()
            else:
                # if we include deprecated, set no filter
                return None

        return super().convert_filter_to_expression(filter_)
