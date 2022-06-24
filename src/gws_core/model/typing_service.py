

from importlib.resources import Resource
from typing import Callable, List, Type

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchParams
from gws_core.model.typing import Typing, TypingNameObj
from gws_core.model.typing_manager import TypingManager
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
               search_builder: TypingSearchBuilder = None) -> Paginator[Typing]:

        if search_builder is None:
            search_builder = TypingSearchBuilder(Typing)

        # force to add a filter hide to False
        search.override_filter_criteria('hide', 'EQ', False)

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_importers(cls, resource_typing_name: str, extension: str,
                         search: SearchParams,
                         page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:

        search_builder = TypingSearchBuilder(TaskTyping)

        # force to add a filter on related typing name
        related_model_type: Type[Resource] = TypingManager.get_type_from_name(resource_typing_name)
        search_builder.add_expression(TaskTyping.get_related_model_expression(related_model_type))

        # force to add a filter on sub type
        importer_sub_type: TaskSubType = 'IMPORTER'
        search_builder.add_expression(TaskTyping.object_sub_type == importer_sub_type)

        # get the importer_ignore_extension and remove it
        ignore_file_extension: bool = search.get_filter_criteria_value('importer_ignore_extension')
        search.remove_filter_criteria('importer_ignore_extension')

        pagination = cls.search(search, page, number_of_items_per_page, search_builder)

        # filter the pagination by extension
        if extension and not ignore_file_extension:
            filter_function: Callable[[TaskTyping],
                                      bool] = lambda t: t.importer_extension_is_supported(extension)

            pagination.filter(filter_function)

        return pagination

    @classmethod
    def search_transformers(cls, resource_typing_names: List[str],
                            search: SearchParams,
                            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:

        search_builder = TypingSearchBuilder(TaskTyping)

        # force to add a filter on related typing name
        related_model_types: List[Type[Resource]] = [TypingManager.get_type_from_name(x) for x in resource_typing_names]
        search_builder.add_expression(TaskTyping.get_related_model_expression(related_model_types))

        # force to add a filter on sub type
        sub_type: TaskSubType = 'TRANSFORMER'
        search_builder.add_expression(TaskTyping.object_sub_type == sub_type)

        pagination = cls.search(search, page, number_of_items_per_page, search_builder)

        return pagination
