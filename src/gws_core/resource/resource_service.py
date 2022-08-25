# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from fastapi.responses import FileResponse
from gws_core.config.config_types import ConfigParamsDict, ConfigSpecs
from gws_core.core.utils.utils import Utils
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.resource_list_base import ResourceListBase
from gws_core.resource.view import View
from gws_core.resource.view_config.view_config import ViewConfig
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
    def get_resource_children(cls, id: str) -> List[ResourceModel]:
        resource_model: ResourceModel = cls.get_resource_by_id(id)

        resource: Resource = resource_model.get_resource()

        if isinstance(resource, ResourceListBase):
            return resource._get_all_resource_models()

        return []

    @classmethod
    def delete(cls, resource_id: str) -> None:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        if resource_model.origin == ResourceOrigin.UPLOADED:
            cls.check_before_resource_update(resource_model)

            resource_model.delete_instance()
        # if the resource was imported or transformed, we delete the experiment that generated it
        elif resource_model.origin == ResourceOrigin.IMPORTED or resource_model.origin == ResourceOrigin.TRANSFORMED:
            experiment: Experiment = resource_model.experiment
            if experiment is None:
                raise BadRequestException("The resource is not associated to an experiment")

            ExperimentService.delete_experiment(experiment.id)

        else:
            raise BadRequestException("Can't delete this resource as it was created by an experiment")

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
        task_model: TaskModel = TaskModel.select().where(TaskModel.source_config_id == resource_model.id).first()

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
                                          save_view_config: bool = False,
                                          view_config: ViewConfig = None) -> Dict:

        resource: Resource = resource_model.get_resource()

        view = await cls.get_view_on_resource(resource, view_name, config_values, transformers)

        view_config: ViewConfig = view_config
        if save_view_config and not view_config:
            view_config = ViewConfigService.save_view_config(
                resource_model, view, view_name, config_values, transformers)

        # call the view to dict
        return {
            "view": ViewHelper.call_view_to_dict(view, config_values),
            "resource_id": resource_model.id,
            "view_config": view_config.to_json() if view_config else None
        }

    @classmethod
    async def call_view_from_view_config(cls, view_config_id: str) -> Dict:
        view_config = ViewConfigService.get_by_id(view_config_id)

        return await cls.call_view_on_resource_model(
            view_config.resource_model, view_name=view_config.view_name, config_values=view_config.config_values,
            transformers=view_config.transformers, save_view_config=False, view_config=view_config)

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
            search_builder.add_expression(ResourceModel.parent_resource_id.is_null())
        search.remove_filter_criteria('include_children_resource')

        # Handle the project filters, get all experiment of this project and filter by experiment
        projects_criteria: SearchFilterCriteria = search.get_filter_criteria('project')
        if projects_criteria is not None:
            experiments: List[Experiment] = list(Experiment.select().where(
                Experiment.project.in_(projects_criteria['value'])))
            search_builder.add_expression(ResourceModel.experiment.in_(experiments))
            search.remove_filter_criteria('project')

        # Handle 'include_intermediate_resource'
        # If not provided or false, filter with resource where show_in_databox = True
        # Otherwise, not filter
        include_non_output: SearchFilterCriteria = search.get_filter_criteria('include_intermediate_resource')
        if include_non_output is None or not include_non_output['value']:
            search_builder.add_expression(ResourceModel.show_in_databox == True)
        search.remove_filter_criteria('include_intermediate_resource')

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    ############################# DOWNLOAD ###########################

    @classmethod
    def download_resource(cls, id: str, exporter_typing_name: str, params: ConfigParamsDict) -> FileResponse:

        fs_node: FSNode = ConverterService.call_exporter_directly(id, exporter_typing_name, params)

        return FileResponse(fs_node.path, media_type='application/octet-stream', filename=fs_node.get_default_name())
