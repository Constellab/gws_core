

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchDict
from gws_core.model.typing import Typing
from gws_core.model.typing_model_search import TypingModelSearchBuilder
from peewee import ModelSelect


class TypingService():

    @classmethod
    def search(cls, search: SearchDict,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:

        search_builder: SearchBuilder = TypingModelSearchBuilder()

        # force to add a filter hide to False
        search.override_filter_criteria('hide', 'EQ', False)

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)
