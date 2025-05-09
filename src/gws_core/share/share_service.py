import threading
from typing import List, Optional, Type, cast

from peewee import JOIN

from gws_core.community.community_service import CommunityService
from gws_core.config.config_params import ConfigParamsDict
from gws_core.core.classes.paginator import Paginator
from gws_core.core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from gws_core.core.utils.logger import Logger
from gws_core.entity_navigator.entity_navigator import EntityNavigatorScenario
from gws_core.external_lab.external_lab_api_service import \
    ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.impl.file.file import File
from gws_core.model.typing_manager import TypingManager
from gws_core.process.process_proxy import ProcessProxy
from gws_core.process.process_types import ProcessStatus
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource import Resource
from gws_core.resource.resource_controller import CallViewParams
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.task.resource_zipper_task import ResourceZipperTask
from gws_core.resource.view.view_result import CallViewResult
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.share.shared_dto import (SharedEntityMode, ShareLinkEntityType,
                                       ShareResourceInfoReponseDTO,
                                       ShareResourceZippedResponseDTO,
                                       ShareScenarioInfoReponseDTO)
from gws_core.share.shared_entity_info import SharedEntityInfo
from gws_core.share.shared_resource import SharedResource
from gws_core.share.shared_scenario import SharedScenario
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.plug.output_task import OutputTask
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import AuthenticateUser
from gws_core.user.user import User

from .share_link import ShareLink


class ShareService():
    """Service to manage communication between lab to share entities
    """

    # version of the share service
    VERSION = 2

    @classmethod
    def get_shared_to_list(
            cls, entity_type: ShareLinkEntityType, entity_id: str,
            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[SharedEntityInfo]:
        """Retrun the list of lab that downloaded the resource
        """

        share_entity_info: Type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

        query = share_entity_info.get_sents(entity_id)

        paginator: Paginator[ShareLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def mark_entity_as_shared(cls, entity_type: ShareLinkEntityType,
                              shared_entity_link: ShareLink, receiver_lab: ExternalLabWithUserInfo) -> None:
        """Method called by an external lab after the an entity was successfully
        import in the external lab. This helps this lab to keep track of which lab downloaded the entity
        """
        share_entity_info: Type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

        # check if this resource was already downloaded by this lab
        if share_entity_info.already_shared_with_lab(shared_entity_link.entity_id, receiver_lab.lab_id):
            return

        share_entity_info.create_from_lab_info(shared_entity_link.entity_id, SharedEntityMode.SENT,
                                               receiver_lab, shared_entity_link.created_by)

    @classmethod
    def _get_shared_entity_type(cls, entity_type: ShareLinkEntityType) -> Type[SharedEntityInfo]:
        """Return the shared entity type
        """
        if entity_type == ShareLinkEntityType.RESOURCE:
            return SharedResource
        elif entity_type == ShareLinkEntityType.SCENARIO:
            return SharedScenario
        else:
            raise Exception(f'Entity type {entity_type} is not supported')

    #################################### RESOURCE ####################################

    @classmethod
    def get_resource_entity_object_info(cls, shared_entity_link: ShareLink) -> ShareResourceInfoReponseDTO:
        """Method for resource model to get the entity object info
        """
        resource_model = ResourceModel.get_by_id_and_check(shared_entity_link.entity_id)

        entity_object: List[ResourceModelDTO] = [resource_model.to_dto()]

        # specific case for resource set that contains multiple resource
        # we need to add all the resource to the zip
        resource = resource_model.get_resource()
        if isinstance(resource, ResourceListBase):
            resource_models = resource.get_resource_models()
            entity_object.extend([resource_model.to_dto() for resource_model in resource_models])

        zip_url: str = ExternalLabApiService.get_current_lab_route(f"share/resource/{shared_entity_link.token}/zip")
        return ShareResourceInfoReponseDTO(version=cls.VERSION, entity_type=shared_entity_link.entity_type,
                                           entity_id=shared_entity_link.entity_id, entity_object=entity_object,
                                           zip_entity_route=zip_url)

    @classmethod
    def zip_shared_resource(cls, shared_entity_link: ShareLink) -> ShareResourceZippedResponseDTO:

        if shared_entity_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        zipped_resource: ResourceModel = cls._zip_resource(shared_entity_link.entity_id, shared_entity_link.created_by)

        # generate the link to download the zipped resource
        download_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/resource/{shared_entity_link.token}/download")
        return ShareResourceZippedResponseDTO(
            version=cls.VERSION, entity_type=shared_entity_link.entity_type, entity_id=shared_entity_link.entity_id,
            zipped_entity_resource_id=zipped_resource.id, download_entity_route=download_url)

    @classmethod
    def _zip_resource(cls, resource_model_id: str, shared_by: User) -> ResourceModel:

        zippped_resource = cls._find_zipped_resource_from_origin_resource(resource_model_id)

        if zippped_resource:
            Logger.info(
                f"Resource {resource_model_id} was already zipped to resource {zippped_resource.id}, using the same zip file.")
            return zippped_resource

        with AuthenticateUser(shared_by):
            return cls.run_zip_resource_exp(resource_model_id, shared_by)

    @classmethod
    def _find_zipped_resource_from_origin_resource(cls, resource_model_id: str) -> Optional[ResourceModel]:
        """Method that find the zipped resource from the origin resource
        """
        # check if the resource was already zipped in this lab for the current version of ResourceZipperTask
        typing = TypingManager.get_typing_from_name_and_check(ResourceZipperTask.get_typing_name())
        task_model: TaskModel = TaskModel.select().where(
            (TaskModel.process_typing_name == typing.typing_name) &
            (TaskModel.status == ProcessStatus.SUCCESS) &
            (TaskModel.brick_version_on_run == typing.brick_version) &
            (TaskInputModel.resource_model == resource_model_id)) \
            .join(TaskInputModel, JOIN.LEFT_OUTER) \
            .first()

        # if the resource was already zipped
        if task_model:
            return task_model.outputs.get_resource_model(ResourceZipperTask.output_name)

        return None

    @classmethod
    def run_zip_resource_exp(cls, id_: str, shared_by: User) -> ResourceModel:
        """Method that zip a resource ands return the new resource
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(id_)

        scenario: ScenarioProxy = ScenarioProxy(
            None, title=f"{resource_model.name} zipper")
        protocol: ProtocolProxy = scenario.get_protocol()

        # Add the importer and the connector
        zipper: ProcessProxy = protocol.add_process(ResourceZipperTask, 'zipper', {'shared_by_id': shared_by.id})

        # Add source and connect it
        protocol.add_resource('source', resource_model.id, zipper << ResourceZipperTask.input_name)

        # Add output task and connect it
        output_task = protocol.add_output('output', zipper >> ResourceZipperTask.output_name, False)

        scenario.run(auto_delete_if_error=True)
        output_task.refresh()

        return output_task.get_input_resource_model(OutputTask.input_name)

    @classmethod
    def download_zipped_resource(cls, shared_entity_link: ShareLink) -> str:
        """Method that is used to download the zipped resource generated by the shared action
        """

        if shared_entity_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        zipped_resource = cls._find_zipped_resource_from_origin_resource(shared_entity_link.entity_id)

        if not zipped_resource:
            raise Exception('The resource was not zipped')

        # retrieve the zipped resource that contains the shared entity
        zip_file: Resource = zipped_resource.get_resource()

        if not isinstance(zip_file, File):
            raise Exception('Zip file is not a file')

        # check that the generated zip resource was generated from the shared entity of the token
        if zip_file.get_technical_info('origin_entity_id').value != shared_entity_link.entity_id:
            raise Exception('Zip file does not contain the shared entity')

        return zip_file.path

    @classmethod
    def call_resource_view(
            cls, shared_entity_link: ShareLink, view_name: str, call_view_params: CallViewParams) -> CallViewResult:
        """Method to call a view on a resource
        """
        if shared_entity_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        view_result = ResourceService.get_and_call_view_on_resource_model(
            shared_entity_link.entity_id, view_name, call_view_params.values, call_view_params.save_view_config)

        # If this is a StreamlitResource, send app statistics to the Community
        if shared_entity_link.entity_type is ShareLinkEntityType.RESOURCE:
            resource = cast(ResourceModel, shared_entity_link.get_model_and_check(
                shared_entity_link.entity_id, shared_entity_link.entity_type)).get_resource()

            if isinstance(resource, StreamlitResource):
                cls._init_send_resource_app_stat_to_community_thread(
                    app_url=shared_entity_link.get_public_link())

        return view_result

    @classmethod
    def _init_send_resource_app_stat_to_community_thread(cls, app_url: str):
        x = threading.Thread(target=cls._send_resource_app_stat_to_community, args=(app_url,))
        x.start()

    @classmethod
    def _send_resource_app_stat_to_community(cls, app_url: str):
        try:
            CommunityService.send_app_stat(app_url)
        except Exception as err:
            Logger.error(f"Error sending app statistics to the Community. Error: {str(err)}")

        #################################### SCENARIO ####################################

    @classmethod
    def get_scenario_entity_object_info(cls, shared_entity_link: ShareLink) -> ShareScenarioInfoReponseDTO:

        scenario = ScenarioService.get_by_id_and_check(shared_entity_link.entity_id)

        if scenario.is_running:
            raise Exception('The scenario is running and downloaded, please wait for the end of the scenario')

        # generate the link to download the zipped resource
        download_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/scenario/{shared_entity_link.token}/resource/[RESOURCE_ID]/zip")
        return ShareScenarioInfoReponseDTO(
            version=cls.VERSION,
            entity_type=shared_entity_link.entity_type,
            entity_id=shared_entity_link.entity_id,
            entity_object=ScenarioService.export_scenario(shared_entity_link.entity_id),
            resource_route=download_url,
            token=shared_entity_link.token,
            origin=ExternalLabApiService.get_current_lab_info(shared_entity_link.created_by)
        )

    @classmethod
    def zip_shared_scenario_resource(
            cls, shared_entity_link: ShareLink, resource_id: str) -> ShareResourceZippedResponseDTO:
        if shared_entity_link.entity_type != ShareLinkEntityType.SCENARIO:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        cls._check_resource_is_in_scenario(shared_entity_link.entity_id, resource_id)

        zipped_resource: ResourceModel = cls._zip_resource(resource_id, shared_entity_link.created_by)

        # generate the link to download the zipped resource
        download_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/scenario/{shared_entity_link.token}/resource/{resource_id}/download")
        return ShareResourceZippedResponseDTO(
            version=cls.VERSION, entity_type=shared_entity_link.entity_type, entity_id=shared_entity_link.entity_id,
            zipped_entity_resource_id=zipped_resource.id, download_entity_route=download_url)

    @classmethod
    def download_scenario_resource(cls, shared_entity_link: ShareLink, resource_id: str) -> str:
        """Method that is used to download the zipped resource generated by the shared action
        """

        if shared_entity_link.entity_type != ShareLinkEntityType.SCENARIO:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        cls._check_resource_is_in_scenario(shared_entity_link.entity_id, resource_id)

        # retrieve the zipped resource
        zipped_resource = cls._find_zipped_resource_from_origin_resource(resource_id)

        if not zipped_resource:
            raise Exception('The resource was not zipped')

        zip_file: Resource = zipped_resource.get_resource()

        if not isinstance(zip_file, File):
            raise Exception('Zip file is not a file')

        return zip_file.path

    @classmethod
    def _check_resource_is_in_scenario(cls, scenario_id: str, resource_id: str) -> None:
        # check that the resource was generated by the scenario or used as input of the scenario

        scenario = ScenarioService.get_by_id_and_check(scenario_id)
        scenario_navigator = EntityNavigatorScenario(scenario)

        if scenario_navigator.get_next_resources().get_as_nav_set().has_entity(resource_id) or \
                scenario_navigator.get_previous_resources().get_as_nav_set().has_entity(resource_id):
            return

        raise UnauthorizedException(f'The resource {resource_id} was not generated by the shared scenario')
