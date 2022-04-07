

from typing import List, Type

from gws_core.core.utils.utils import Utils
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource import Resource
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
        # Special case to filter on relate_model and parent of the model
        elif filter_['key'] == 'related_model_typing_name':
            related_model_type: Type[Typing] = TypingManager.get_type_from_name(filter_['value'])
            # get all the class types between base_type and Model
            parent_classes: List[Type[Resource]] = Utils.get_parent_classes(related_model_type, Resource)

            typings_names = [parent._typing_name for parent in parent_classes]

            return Typing.related_model_typing_name.in_(typings_names)

        return super().get_filter_expression(filter_)
