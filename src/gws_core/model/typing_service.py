

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchDict
from gws_core.model.typing import Typing, TypingNameObj
from gws_core.model.typing_search_builder import TypingSearchBuilder
from gws_core.protocol.protocol_typing import ProtocolTyping
from gws_core.resource.resource_typing import ResourceTyping
from gws_core.task.task_typing import TaskTyping
from peewee import ModelSelect


class TypingService():

    @classmethod
    def get_typing(cls, typing_name: str) -> Typing:
        typing_name_obj: TypingNameObj = TypingNameObj.from_typing_name(typing_name)

        if typing_name_obj.object_type == 'TASK':
            return TaskTyping.get_by_typing_name(typing_name)
        elif typing_name_obj.object_type == 'PROTOCOL':
            return ProtocolTyping.get_by_typing_name(typing_name)
        elif typing_name_obj.object_type == 'RESOURCE':
            return ResourceTyping.get_by_typing_name(typing_name)
        else:
            return Typing.get_by_typing_name(typing_name)

    @classmethod
    def search(cls, search: SearchDict,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:

        search_builder: SearchBuilder = TypingSearchBuilder()

        # force to add a filter hide to False
        search.override_filter_criteria('hide', 'EQ', False)

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)
