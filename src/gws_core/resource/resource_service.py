# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from fastapi.responses import FileResponse
from gws_core.config.config_types import ConfigParamsDict, ConfigSpecs
from gws_core.core.utils.utils import Utils
from gws_core.experiment.experiment import Experiment
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.view import View
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.task_model import TaskModel
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import (SearchBuilder, SearchFilterCriteria,
                                           SearchParams)
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.service.base_service import BaseService
from ..model.typing_manager import TypingManager
from ..resource.view_helper import ViewHelper
from ..task.task_input_model import TaskInputModel
from ..task.transformer.transformer_service import TransformerService
from ..task.transformer.transformer_type import TransformerDict
from .resource_model import Resource, ResourceModel, ResourceOrigin
from .resource_model_search_builder import ResourceModelSearchBuilder
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
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def delete(cls, resource_id: str) -> None:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        cls.check_before_resource_update(resource_model)

        resource_model.delete_instance()

    @classmethod
    def check_before_resource_update(cls, resource_model: ResourceModel) -> None:
        """Method to check if a resource is updatable
        """
        if resource_model.origin != ResourceOrigin.UPLOADED:
            raise BadRequestException(GWSException.DELETE_GENERATED_RESOURCE_ERROR.value,
                                      GWSException.DELETE_GENERATED_RESOURCE_ERROR.value)

        # Check if resource is used as input of a task
        task_input: TaskInputModel = TaskInputModel.get_by_resource_model(resource_model.id).first()

        if task_input:
            raise BadRequestException(GWSException.RESOURCE_USED_ERROR.value,
                                      unique_code=GWSException.RESOURCE_USED_ERROR.value,
                                      detail_args={"experiment": task_input.experiment.get_short_name()})

        # Check if resource is used as Config of a Source Task
        task_model: TaskModel = TaskModel.select().where(TaskModel.source_config == resource_model.id).first()

        if task_model:
            raise BadRequestException(GWSException.RESOURCE_USED_ERROR.value,
                                      unique_code=GWSException.RESOURCE_USED_ERROR.value,
                                      detail_args={"experiment": task_model.experiment.get_short_name()})

    @classmethod
    def update_name(cls, resource_model_id: str, name: str) -> ResourceModel:
        resource_model: ResourceModel = cls.get_resource_by_id(resource_model_id)

        resource_model.name = name
        return resource_model.save()

    @classmethod
    def update_resource_type(cls, file_id: str, file_typing_name: str) -> ResourceModel:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(file_id)

        ResourceService.check_before_resource_update(resource_model)

        file_type: Type[Resource] = TypingManager.get_type_from_name(file_typing_name)

        if not Utils.issubclass(file_type, Resource):
            raise BadRequestException('The type must be a Resource')

        resource_model.resource_typing_name = file_type._typing_name
        return resource_model.save()

    @classmethod
    def get_experiments_resources(cls, experiment_ids: List[str]) -> List[ResourceModel]:
        """Return the list of reosurces used as input or output by the experiments

        :param experiments: _description_
        :type experiments: List[str]
        :return: _description_
        :rtype: List[ResourceModel]
        """
        generated_resources = cls.get_experiment_output_resources(experiment_ids)

        task_inputs = cls.get_experiment_input_resources(experiment_ids)

        resources: Dict[str, ResourceModel] = {}

        for resource in generated_resources + task_inputs:
            resources[resource.id] = resource

        return list(resources.values())

    @classmethod
    def get_experiment_output_resources(cls, experiment_ids: List[str]) -> List[ResourceModel]:
        return list(ResourceModel.get_by_experiments(experiment_ids))

    @classmethod
    def get_experiment_input_resources(cls, experiment_ids: List[str]) -> List[ResourceModel]:
        task_inputs: List[TaskInputModel] = list(TaskInputModel.get_by_experiments(experiment_ids))
        return [task_input.resource_model for task_input in task_inputs]

    ############################# RESOURCE TYPE ###########################

    @classmethod
    def fetch_resource_type_list(cls) -> List[ResourceTyping]:
        return list(ResourceTyping.get_types())

    ################################# VIEW ###############################

    @classmethod
    def get_views_of_resource(cls, resource_model_id: str) -> List[ResourceViewMetaData]:
        resource_model: ResourceModel = cls.get_resource_by_id(resource_model_id)

        return cls.get_views_of_resource_type(resource_model.get_resource_type())

    @classmethod
    def get_views_of_resource_type(cls, resource_type: Type[Resource]) -> List[ResourceViewMetaData]:
        if not issubclass(resource_type, Resource):
            raise BadRequestException("Can't find views of an object other than a Resource")
        return ViewHelper.get_views_of_resource_type(resource_type)

    @classmethod
    def get_view_specs(cls, resource_model_id: str, view_name: str) -> ConfigSpecs:
        resource_model: ResourceModel = cls.get_resource_by_id(resource_model_id)

        return ViewHelper.get_view_specs(resource_model, view_name)

    @classmethod
    async def get_and_call_view_on_resource_model(cls, resource_model_id: str,
                                                  view_name: str, config_values: Dict[str, Any],
                                                  transformers: List[TransformerDict],
                                                  save_view_config: bool = False) -> Dict:

        resource_model: ResourceModel = cls.get_resource_by_id(resource_model_id)
        return await cls.call_view_on_resource_model(resource_model, view_name, config_values, transformers, save_view_config)

    @classmethod
    async def call_view_on_resource_model(cls, resource_model: ResourceModel,
                                          view_name: str, config_values: Dict[str, Any],
                                          transformers: List[TransformerDict],
                                          save_view_config: bool = False) -> Dict:

        resource: Resource = resource_model.get_resource()

        view = await cls.get_view_on_resource(resource, view_name, config_values, transformers)

        if save_view_config:
            ViewConfigService.save_view_config_in_async(
                resource_model, view, view_name, config_values, transformers)

        # call the view to dict
        return ViewHelper.call_view_to_dict(view, config_values)

    @classmethod
    async def get_view_on_resource(cls, resource: Resource,
                                   view_name: str, config_values: Dict[str, Any],
                                   transformers: List[TransformerDict] = None) -> View:

        # if there is a transformer, call it before calling the view
        if transformers is not None and len(transformers) > 0:
            resource = await TransformerService.call_transformers(resource, transformers)

        return ViewHelper.generate_view_on_resource(resource, view_name, config_values)

    ############################# SEARCH ###########################

    @classmethod
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ResourceModelSearchBuilder()

        # Handle the children resource
        criteria: SearchFilterCriteria = search.get_filter_criteria('include_children_resource')

        # if the criteria is not provided or False, we don't include the children
        if criteria is None or not criteria['value']:
            search_builder.add_expression(ResourceModel.parent_resource.is_null())
        search.remove_filter_criteria('include_children_resource')

        # Handle the project filters, get all experiment of this project and filter by experiment
        projects_criteria: SearchFilterCriteria = search.get_filter_criteria('project')
        if projects_criteria is not None:
            experiments: List[Experiment] = Experiment.select().where(Experiment.project == projects_criteria['value'])
            search_builder.add_expression(ResourceModel.experiment.in_(experiments))
            search.remove_filter_criteria('project')

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    ############################# DOWNLOAD ###########################

    @classmethod
    def download_resource(cls, id: str, exporter_typing_name: str, params: ConfigParamsDict) -> FileResponse:

        fs_node: FSNode = ConverterService.call_exporter_directly(id, exporter_typing_name, params)

        return FileResponse(fs_node.path, media_type='application/octet-stream', filename=fs_node.get_default_name())
