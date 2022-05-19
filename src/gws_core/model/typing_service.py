

from typing import Callable, Type

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchParams
from gws_core.model.typing import Typing, TypingNameObj
from gws_core.model.typing_search_builder import TypingSearchBuilder
from gws_core.protocol.protocol_typing import ProtocolTyping
from gws_core.resource.resource_typing import ResourceTyping
from gws_core.task.task_typing import TaskSubType, TaskTyping
from peewee import ModelSelect
from regex import B


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
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20,
               type_: Type[Typing] = Typing) -> Paginator[Typing]:

        search_builder: SearchBuilder = TypingSearchBuilder(type_)

        # force to add a filter hide to False
        search.override_filter_criteria('hide', 'EQ', False)

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_importers(cls, resource_typing_name: str, extension: str,
                         search: SearchParams,
                         page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:
        # force to add a filter on related typing name
        search.override_filter_criteria('related_model_typing_name', 'EQ', resource_typing_name)

        # force to add a filter on sub type
        importer_sub_type: TaskSubType = 'IMPORTER'
        search.override_filter_criteria('object_sub_type', 'EQ', importer_sub_type)

        ignore_file_extension: bool = search.get_filter_criteria_value('importer_ignore_extension')
        search.remove_filter_criteria('importer_ignore_extension')

        pagination = cls.search(search, page, number_of_items_per_page, TaskTyping)

        # filter the pagination by extension
        if extension and not ignore_file_extension:
            filter_function: Callable[[TaskTyping],
                                      bool] = lambda t: t.importer_extension_is_supported(extension)

            pagination.filter(filter_function)

        return pagination

    @classmethod
    def search_transformers(cls, resource_typing_name: str,
                            search: SearchParams,
                            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:
        # force to add a filter on related typing name
        search.override_filter_criteria('related_model_typing_name', 'EQ', resource_typing_name)

        # force to add a filter on sub type
        sub_type: TaskSubType = 'TRANSFORMER'
        search.override_filter_criteria('object_sub_type', 'EQ', sub_type)

        pagination = cls.search(search, page, number_of_items_per_page)

        return pagination
