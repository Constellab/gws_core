# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from gws_core.task.task import Task
from gws_core.task.task_runner import TaskRunner
from gws_core.task.transformer.transformer import TransformerDict
from gws_core.task.transformer.transformer_service import TransformerService
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchDict
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.service.base_service import BaseService
from ..model.typing_manager import TypingManager
from ..resource.view_helper import ViewHelper
from ..task.task_input_model import TaskInputModel
from .resource_model import Resource, ResourceModel, ResourceOrigin
from .resource_model_search import ResourceModelSearchBuilder
from .resource_typing import ResourceTyping
from .view_meta_data import ResourceViewMetaData


class ResourceService(BaseService):

    ############################# RESOURCE MODEL ###########################

    @classmethod
    def get_resource_by_id(cls, id: str) -> ResourceModel:
        return ResourceModel.get_by_id_and_check(id)

    @classmethod
    def get_resources_of_type(cls,
                              resource_typing_name: str,
                              page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        # request the resource model
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        # Get the resource models and filter them with resource type
        # TODO problem, it does select sub class of resource type.
        query = ResourceModel.select_by_resource_typing_name(resource_typing_name)\
            .order_by(ResourceModel.created_at.desc())

        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def delete(cls, resource_id: str) -> None:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        cls.check_before_resource_update(resource_model)

        resource_model.delete_instance()

    @classmethod
    def check_before_resource_update(cls, resource_model: ResourceModel) -> None:
        """Method to check if a resource is updatable
        """
        if resource_model.origin != ResourceOrigin.IMPORTED:
            raise BadRequestException(GWSException.DELETE_GENERATED_RESOURCE_ERROR.value,
                                      GWSException.DELETE_GENERATED_RESOURCE_ERROR.value)

        task_input: TaskInputModel = TaskInputModel.get_by_resource_model(resource_model.id).first()

        if task_input:
            raise BadRequestException(GWSException.RESOURCE_USED_ERROR.value,
                                      unique_code=GWSException.RESOURCE_USED_ERROR.value,
                                      detail_args={"experiment": task_input.experiment.get_short_name()})

    ############################# RESOURCE TYPE ###########################

    @classmethod
    def fetch_resource_type_list(cls) -> List[ResourceTyping]:

        return list(ResourceTyping.get_types())

    ################################# VIEW ###############################

    @classmethod
    def get_views_of_resource(cls, resource_typing_name: str) -> List[ResourceViewMetaData]:
        resource_type: Type[Resource] = TypingManager.get_type_from_name(resource_typing_name)

        return cls.get_views_of_resource_type(resource_type)

    @classmethod
    def get_views_of_resource_type(cls, resource_type: Type[Resource]) -> List[ResourceViewMetaData]:
        if not issubclass(resource_type, Resource):
            raise BadRequestException("Can't find views of an object other than a Resource")
        return ViewHelper.get_views_of_resource_type(resource_type)

    @classmethod
    async def call_view_on_resource_type(cls, resource_model_id: str,
                                         view_name: str, config_values: Dict[str, Any],
                                         transformers: List[TransformerDict]) -> Any:

        resource_model: ResourceModel = cls.get_resource_by_id(resource_model_id)

        resource: Resource = resource_model.get_resource()
        return await cls.call_view_on_resource(resource, view_name, config_values, transformers)

    @classmethod
    async def call_view_on_resource(cls, resource: Resource,
                                    view_name: str, config_values: Dict[str, Any],
                                    transformers: List[TransformerDict] = None) -> Any:
        # if there is a transformer, call it before calling the view
        if transformers is not None and len(transformers) > 0:
            resource = await TransformerService.call_transformers(resource, transformers)

        return ViewHelper.call_view_on_resource(resource, view_name, config_values)

    ############################# SEARCH ###########################

    @classmethod
    def search(cls, search: SearchDict,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ResourceModelSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)
