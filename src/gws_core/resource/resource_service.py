

from typing import Any, Callable, Dict, List, Optional, Type

from gws_core.config.config_params import ConfigParamsDict
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.utils import Utils
from gws_core.entity_navigator.entity_navigator import EntityNavigatorResource
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.table.table import Table
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.view.view_dto import ResourceViewMetadatalDTO, ViewDTO
from gws_core.resource.view.view_result import CallViewResult
from gws_core.resource.view.view_runner import ViewRunner
from gws_core.resource.view.view_types import exluded_views_in_note
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.share.shared_resource import SharedResource
from gws_core.user.current_user_service import CurrentUserService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import (SearchBuilder, SearchFilterCriteria,
                                           SearchParams)
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..model.typing_manager import TypingManager
from ..task.task_input_model import TaskInputModel
from .resource_model import Resource, ResourceModel
from .resource_search_builder import ResourceSearchBuilder
from .view.view_helper import ViewHelper
from .view.view_meta_data import ResourceViewMetaData


class ResourceService():

    ############################# UPDATE RESOURCE MODEL ###########################
    @classmethod
    def delete(cls, resource_id: str) -> None:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(
            resource_id)

        resource_model.delete_instance()

    @classmethod
    def _check_before_resource_update(cls, resource_model: ResourceModel) -> None:
        """Method to check if a resource is updatable
        """
        if not resource_model.is_manually_generated():
            raise BadRequestException(GWSException.DELETE_GENERATED_RESOURCE_ERROR.value,
                                      GWSException.DELETE_GENERATED_RESOURCE_ERROR.value)

        cls.check_if_resource_is_used(resource_model)

    @classmethod
    def check_if_resource_is_used(cls, resource_model: ResourceModel) -> None:
        """Check if a resource is used in a scenario, raise an exception if it is the case
        """
        resource_navigation = EntityNavigatorResource(resource_model)
        next_scenario = resource_navigation.get_next_scenarios().get_first_entity()

        if next_scenario:
            raise BadRequestException(GWSException.RESOURCE_USED_ERROR.value,
                                      unique_code=GWSException.RESOURCE_USED_ERROR.value,
                                      detail_args={"scenario": next_scenario.get_short_name()})

    @classmethod
    def update_name(cls, resource_model_id: str, name: str) -> ResourceModel:
        resource_model: ResourceModel = cls.get_by_id_and_check(resource_model_id)

        if resource_model.origin == ResourceOrigin.S3_FOLDER_STORAGE:
            raise BadRequestException(
                "This resource is a document of the folder in the space, it can't be renamed.")

        resource = resource_model.get_resource()
        resource.set_name(name)
        resource_model.name = resource.get_name()
        return resource_model.save()

    @classmethod
    def update_resource_type(cls, file_id: str, file_typing_name: str) -> ResourceModel:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(
            file_id)

        ResourceService._check_before_resource_update(resource_model)

        file_type: Type[Resource] = TypingManager.get_and_check_type_from_name(
            file_typing_name)

        if not Utils.issubclass(file_type, Resource):
            raise BadRequestException('The type must be a Resource')

        resource_model.set_resource_typing_name(file_type.get_typing_name())

        # check that the resource can be loaded and is valid
        resource: Resource = resource_model.get_resource()
        resource.check_resource()

        return resource_model.save()

    @classmethod
    def update_flagged(cls, view_config_id: str, flagged: bool) -> ResourceModel:
        resource_model: ResourceModel = cls.get_by_id_and_check(view_config_id)

        if resource_model.content_is_deleted:
            raise BadRequestException(
                "Can't update the flagged status if the content of the resource is deleted")
        resource_model.flagged = flagged
        return resource_model.save()

    @classmethod
    def update_folder(cls, resource_id: str, folder_id: Optional[str]) -> ResourceModel:
        resource_model: ResourceModel = cls.get_by_id_and_check(resource_id)

        if resource_model.origin == ResourceOrigin.S3_FOLDER_STORAGE:
            raise BadRequestException(
                "This resource is a document of the folder in the space, it can't be moved to another folder.")

        if resource_model.scenario is not None:
            raise BadRequestException(
                "Can't update the folder of a resource that was generated by a scenario")

        folder: SpaceFolder = SpaceFolder.get_by_id_and_check(
            folder_id) if folder_id else None
        resource_model.folder = folder
        return resource_model.save()
    ############################# GET RESOURCE MODEL ###########################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> ResourceModel:
        return ResourceModel.get_by_id_and_check(id)

    @classmethod
    def get_resource_children(cls, id: str) -> List[ResourceModel]:
        resource_model: ResourceModel = cls.get_by_id_and_check(id)

        resource: Resource = resource_model.get_resource()

        if isinstance(resource, ResourceListBase):
            return resource.get_resource_models()

        return []

    @classmethod
    def get_scenarios_resources(cls, scenario_ids: List[str]) -> List[ResourceModel]:
        """Return the list of reosurces used as input or output by the scenarios

        :param scenarios: _description_
        :type scenarios: List[str]
        :return: _description_
        :rtype: List[ResourceModel]
        """
        generated_resources = cls.get_scenario_generated_resources(
            scenario_ids)

        task_inputs = cls.get_scenario_input_resources(scenario_ids)

        return list(set(generated_resources + task_inputs))

    @classmethod
    def get_scenario_generated_resources(cls, scenario_ids: List[str]) -> List[ResourceModel]:
        return list(ResourceModel.get_by_scenarios(scenario_ids))

    @classmethod
    def get_scenario_input_resources(cls, scenario_ids: List[str]) -> List[ResourceModel]:
        task_inputs: List[TaskInputModel] = list(
            TaskInputModel.get_by_scenarios(scenario_ids))
        return [task_input.resource_model for task_input in task_inputs]

    ################################# VIEW ###############################

    @classmethod
    def get_views_of_resource(cls, resource_typing_name: str) -> List[ResourceViewMetaData]:
        resource_type = TypingManager.get_and_check_type_from_name(resource_typing_name)

        if not Utils.issubclass(resource_type, Resource):
            raise BadRequestException(
                'The provided type is not a Resource type')

        return cls.get_views_of_resource_type(resource_type)

    @classmethod
    def get_views_of_resource_type(cls, resource_type: Type[Resource]) -> List[ResourceViewMetaData]:
        if not issubclass(resource_type, Resource):
            raise BadRequestException(
                "Can't find views of an object other than a Resource")
        return ViewHelper.get_views_of_resource_type(resource_type)

    @classmethod
    def get_view_specs_from_resource(cls, resource_model_id: str, view_name: str) -> ResourceViewMetadatalDTO:
        resource_model: ResourceModel = cls.get_by_id_and_check(resource_model_id)

        resource = resource_model.get_resource()
        view_meta = ViewHelper.get_and_check_view_meta(type(resource), view_name)

        return view_meta.to_dto()

    @classmethod
    def get_view_specs_from_type(cls, resource_typing_name: str, view_name: str) -> ResourceViewMetadatalDTO:
        resource_type: Type[Resource] = TypingManager.get_and_check_type_from_name(
            resource_typing_name)

        view_meta = ViewHelper.get_and_check_view_meta(
            resource_type, view_name)

        return view_meta.to_dto()

    @classmethod
    def get_and_call_view_on_resource_model(cls, resource_model_id: str,
                                            view_name: str, config_values: ConfigParamsDict,
                                            save_view_config: bool = False) -> CallViewResult:

        resource_model: ResourceModel = cls.get_by_id_and_check(
            resource_model_id)
        return cls.call_view_on_resource_model(resource_model, view_name, config_values, save_view_config)

    @classmethod
    def get_view_json_file(cls, resource_model_id: str,
                           view_name: str, config_values: ConfigParamsDict,
                           save_view_config: bool = False) -> ViewDTO:
        resource_model: ResourceModel = cls.get_by_id_and_check(resource_model_id)
        view = cls.call_view_on_resource_model(resource_model, view_name, config_values, save_view_config).view
        if view.type in list(map(lambda x: x.value, exluded_views_in_note)):
            raise BadRequestException(
                f"View '{view_name}' is not supported to be exported as a file.")
        return view

    @classmethod
    def call_view_on_resource_model(cls, resource_model: ResourceModel,
                                    view_name: str, config_values: ConfigParamsDict,
                                    save_view_config: bool = False) -> CallViewResult:

        resource: Resource = resource_model.get_resource()

        view_runner: ViewRunner = ViewRunner(resource, view_name, config_values)

        view = view_runner.generate_view()

        # call the view to dict
        view_dto = view_runner.call_view_to_dto()

        view_title = view.get_title() or resource.name

        style = view.get_style() or view_runner.get_metadata_style()
        # Save the view config
        view_config: ViewConfig = None
        if save_view_config and CurrentUserService.get_current_user():
            view_config = ViewConfigService.save_view_config(
                resource_model=resource_model,
                view=view,
                view_name=view_name,
                config=view_runner.get_config(),
                view_style=style)

            if view_config:
                # use the title of the view config if it's provided
                view_title = view_config.title

        return CallViewResult(view_dto, resource_model.id, view_config,
                              view_title, view.get_type(), style)

    @classmethod
    def call_view_from_view_config(cls, view_config_id: str) -> CallViewResult:
        view_config = ViewConfigService.get_by_id(view_config_id)

        resource: Resource = view_config.resource_model.get_resource()

        view_runner: ViewRunner = ViewRunner(resource, view_config.view_name, view_config.get_config_values())

        view = view_runner.generate_view()

        # call the view to dict
        view_dto = view_runner.call_view_to_dto()

        # Update view config last call date
        view_config.last_modified_at = DateHelper.now_utc()
        view_config.save()

        return CallViewResult(view_dto, view_config.resource_model.id, view_config, view_config.title,
                              view.get_type(), view_runner.get_metadata_style())

    ############################# SEARCH ###########################

    @classmethod
    def search_by_name(cls, name: str, page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:
        search_builder: SearchBuilder = ResourceSearchBuilder()

        search_builder.add_expression(ResourceModel.name.contains(name))

        return search_builder.search_page(page, number_of_items_per_page)

    @classmethod
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ResourceSearchBuilder()

        # Handle the children resource
        criteria: SearchFilterCriteria = search.get_filter_criteria(
            'include_children_resource')

        # if the criteria is not provided or False, we don't include the children
        if criteria is None or not criteria.value:
            search_builder.add_expression(
                ResourceModel.parent_resource_id.is_null())
        search.remove_filter_criteria('include_children_resource')

        # Handle 'include_not_flagged'
        # If not provided or false, filter with resource where flagged = True
        # Otherwise, not filter
        include_non_output: SearchFilterCriteria = search.get_filter_criteria(
            'include_not_flagged')
        if include_non_output is None or not include_non_output.value:
            search_builder.add_expression(ResourceModel.flagged == True)
        search.remove_filter_criteria('include_not_flagged')

        # Handle 'column_tags'
        column_tags: SearchFilterCriteria = search.get_filter_criteria(
            'column_tags')
        column_tags_filter_function: Callable[[ResourceModel], bool] = None
        if column_tags is not None and column_tags.value:
            column_tags_filter_function: Callable[[ResourceModel],
                                                  bool] = lambda table_resource_model: cls.check_column_tags(
                table_resource_model, column_tags.value)
            search.remove_filter_criteria('column_tags')

        pagination = search_builder.add_search_params(search).search_page(
            page, number_of_items_per_page)
        if column_tags_filter_function is not None:
            pagination.filter(column_tags_filter_function, number_of_items_per_page)
        return pagination

    @classmethod
    def check_column_tags(cls, table_resource_model: ResourceModel, filter_column_tags: List[Any]) -> bool:
        if (table_resource_model.resource_typing_name != 'RESOURCE.gws_core.Table'):
            return False

        table: Table = table_resource_model.get_resource()

        for filter_column_tag in filter_column_tags:
            key = filter_column_tag['key']
            value: str = filter_column_tag['value']
            if value is not None:
                value = value.strip().lower()

            not_found = True
            for column_tag in table.get_column_tags():
                if key in column_tag and value in column_tag[key]:
                    not_found = False
                    break
            if not_found:
                return False

        return True

    ############################# SHARED RESOURCE ###########################

    @classmethod
    def get_shared_resource_origin_info(cls, resource_model_id: str) -> SharedResource:
        return SharedResource.get_and_check_entity_origin(resource_model_id)
