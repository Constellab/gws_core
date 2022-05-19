

from typing import List, Type

from gws_core.core.utils.utils import Utils
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource import Resource
from gws_core.task.task_typing import TaskTyping
from peewee import Expression
from playhouse.mysql_ext import Match

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
            return Match(
                (self._model_type.human_name, self._model_type.short_description, self._model_type.unique_name),
                filter_['value'],
                modifier='IN BOOLEAN MODE')
        # Special case to filter on relate_model and parent of the model
        elif filter_['key'] == 'related_model_typing_name':

            if issubclass(self._model_type, TaskTyping):
                related_model_type: Type[Typing] = TypingManager.get_type_from_name(filter_['value'])

                return self._model_type.get_related_model_expression(related_model_type)
            else:
                return None

        elif filter_['key'] == 'include_deprecated':
            if not filter_['value']:
                return self._model_type.deprecated_since.is_null()
            else:
                # if we include deprecated, set no filter
                return None

        return super().convert_filter_to_expression(filter_)
