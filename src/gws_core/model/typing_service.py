

from typing import Callable, Dict, List, Literal, Type

from peewee import ModelSelect

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.utils import Utils
from gws_core.io.io_spec import IOSpec
from gws_core.model.typing import Typing, TypingNameObj
from gws_core.model.typing_dict import TypingObjectType, TypingStatus
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_search_builder import TypingSearchBuilder
from gws_core.process.process import Process
from gws_core.protocol.protocol_typing import ProtocolTyping
from gws_core.resource.resource import Resource
from gws_core.resource.resource_typing import ResourceTyping
from gws_core.task.task_typing import TaskSubType, TaskTyping


def filter_typing_by_specs(typing: Typing, resource_types: List[Type[Resource]],
                           check_io: Literal['inputs', 'outputs']) -> bool:
    """
    Filter a process typing by its specs (inputs or outputs). Return true if the specs contains a resource types
    that is stricly equals to one of the provided resource_types.
    """
    process_type: Type[Process] = typing.get_type()

    # if the type does not exist or is not a process, we return false
    if not process_type or not Utils.issubclass(process_type, Process):
        return False

    # get the corresponding io spec
    io_specs: Dict[str, IOSpec] = process_type.get_input_specs(
    ) if check_io == 'inputs' else process_type.get_output_specs()

    for spec in io_specs.values():
        io_resource_types = spec.resource_types
        # return true only if one of the resource type is equals one of resource types in specs
        for resource_type in resource_types:
            if resource_type in io_resource_types:
                return True
    return False


class TypingService():

    @classmethod
    def get_typing(cls, typing_name: str) -> Typing:
        typing_name_obj: TypingNameObj = TypingNameObj.from_typing_name(typing_name)

        typing_type: Type[Typing] = cls._get_typing_type_from_obj_type(typing_name_obj.object_type)

        typing: Typing = typing_type.get_by_typing_name(typing_name)

        if typing is None:
            raise BadRequestException(
                f"Can't find the typing with name '{typing_name}', did you register the name with corresponding decorator ?")
        return typing

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
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def suggest_process(cls, search: SearchParams, resource_typing_names: List[str],
                        check_io: Literal['inputs', 'outputs'],
                        page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:
        """
        Suggest a process based on resources types. It filters process either on input or output specs.
        Only return process that have at least one input or output has on of the resource type in the list.
        """

        search_builder = TypingSearchBuilder(Typing)

        pagination = cls.search(search, page, number_of_items_per_page, search_builder)

        # convert resource_typing_names to resource types
        resource_types: List[Type[Resource]] = [
            TypingManager.get_type_from_name(x) for x in resource_typing_names]

        # filter the pagination task input
        filter_function: Callable[[Typing],
                                  bool] = lambda t: filter_typing_by_specs(t, resource_types, check_io)
        pagination.filter(filter_function, number_of_items_per_page / 2)

        return pagination

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

        # filter the pagination by extension manually after the search
        if extension and not ignore_file_extension:
            filter_function: Callable[[TaskTyping],
                                      bool] = lambda t: t.importer_extension_is_supported(extension)

            pagination.filter(filter_function, number_of_items_per_page / 2)

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

    @classmethod
    def delete_unavailable_typings(cls, brick_name: str = None) -> List[str]:
        """
        Remove typing names that are not available in the database
        """

        typing_names: List[Typing] = None

        if brick_name:
            typing_names = list(Typing.select().where(Typing.brick == brick_name))
        else:
            typing_names = list(Typing.select())

        unavailable_types: List[Typing] = [x for x in typing_names if x.get_type_status() == TypingStatus.UNAVAILABLE]

        for typing in unavailable_types:
            typing.delete_instance()

    @classmethod
    def search_type_by_name(cls, object_type: TypingObjectType,  name: str,
                            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceTyping]:
        typing_type: Type[Typing] = cls._get_typing_type_from_obj_type(object_type)
        return Paginator(typing_type.get_by_object_type_and_name(object_type, name),
                         page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_typing_by_object_type(cls, object_type: TypingObjectType,
                                  page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Typing]:
        typing_type: Type[Typing] = cls._get_typing_type_from_obj_type(object_type)
        return Paginator(typing_type.get_by_object_type(object_type),
                         page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def _get_typing_type_from_obj_type(cls, object_type: TypingObjectType) -> Type[Typing]:
        if object_type == 'TASK':
            return TaskTyping
        elif object_type == 'PROTOCOL':
            return ProtocolTyping
        elif object_type == 'RESOURCE':
            return ResourceTyping
        else:
            return Typing
