import threading
from typing import cast

from gws_core.apps.app_resource import AppResource
from gws_core.community.community_service import CommunityService
from gws_core.core.classes.paginator import Paginator
from gws_core.core.exception.exceptions.unauthorized_exception import UnauthorizedException
from gws_core.core.utils.logger import Logger
from gws_core.entity_navigator.entity_navigator import EntityNavigatorScenario
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.impl.file.file import File
from gws_core.process.process_proxy import ProcessProxy
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource import Resource
from gws_core.resource.resource_controller import CallViewParams
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.task.resource_zipper_task import ResourceZipperTask
from gws_core.resource.view.view_result import CallViewResult
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_search_builder import ScenarioSearchBuilder
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.share.shared_dto import (
    SharedEntityMode,
    ShareLinkEntityType,
    ShareResourceInfoReponseDTO,
    ShareResourceZippedResponseDTO,
    ShareScenarioInfoReponseDTO,
)
from gws_core.share.shared_entity_info import SharedEntityInfo
from gws_core.share.shared_resource import SharedResource
from gws_core.share.shared_scenario import SharedScenario
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.task.plug.output_task import OutputTask
from gws_core.user.current_user_service import AuthenticateUser
from gws_core.user.user import User

from .share_link import ShareLink


class ShareService:
    """Service to manage communication between lab to share entities"""

    # version of the share service
    VERSION = 2

    # Tag keys used to identify zip scenarios
    TAG_KEY_ZIP_SCENARIO = "zip-scenario"
    TAG_KEY_ZIP_SCENARIO_VALUE = "true"
    TAG_KEY_ZIP_RESOURCE_ID = "zip-resource-id"
    TAG_KEY_ZIP_TASK_VERSION = "zip-task-version"

    @classmethod
    def get_shared_to_list(
        cls,
        entity_type: ShareLinkEntityType,
        entity_id: str,
        page: int = 0,
        number_of_items_per_page: int = 20,
    ) -> Paginator[SharedEntityInfo]:
        """Retrun the list of lab that downloaded the resource"""

        share_entity_info: type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

        query = share_entity_info.get_sents(entity_id)

        paginator: Paginator[ShareLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page
        )
        return paginator

    @classmethod
    def mark_entity_as_shared(
        cls,
        entity_type: ShareLinkEntityType,
        shared_entity_link: ShareLink,
        receiver_lab: ExternalLabWithUserInfo,
    ) -> None:
        """Method called by an external lab after the an entity was successfully
        import in the external lab. This helps this lab to keep track of which lab downloaded the entity
        """
        share_entity_info: type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

        # check if this resource was already downloaded by this lab
        if share_entity_info.already_shared_with_lab(
            shared_entity_link.entity_id, receiver_lab.lab
        ):
            return

        share_entity_info.create_from_lab_info(
            shared_entity_link.entity_id,
            SharedEntityMode.SENT,
            receiver_lab,
            shared_entity_link.created_by,
        )

    @classmethod
    def _get_shared_entity_type(cls, entity_type: ShareLinkEntityType) -> type[SharedEntityInfo]:
        """Return the shared entity type"""
        if entity_type == ShareLinkEntityType.RESOURCE:
            return SharedResource
        elif entity_type == ShareLinkEntityType.SCENARIO:
            return SharedScenario
        else:
            raise Exception(f"Entity type {entity_type} is not supported")

    #################################### RESOURCE ####################################

    @classmethod
    def get_resource_entity_object_info(
        cls, shared_entity_link: ShareLink
    ) -> ShareResourceInfoReponseDTO:
        """Method for resource model to get the entity object info"""
        resource_model = ResourceModel.get_by_id_and_check(shared_entity_link.entity_id)

        entity_object: list[ResourceModelDTO] = [resource_model.to_dto()]

        # specific case for resource set that contains multiple resource
        # we need to add all the resource to the zip
        resource = resource_model.get_resource()
        if isinstance(resource, ResourceListBase):
            resource_models = resource.get_resource_models()
            entity_object.extend([resource_model.to_dto() for resource_model in resource_models])

        zip_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/resource/{shared_entity_link.token}/zip"
        )
        return ShareResourceInfoReponseDTO(
            version=cls.VERSION,
            entity_type=shared_entity_link.entity_type,
            entity_id=shared_entity_link.entity_id,
            entity_object=entity_object,
            zip_entity_route=zip_url,
        )

    @classmethod
    def zip_shared_resource(cls, shared_entity_link: ShareLink) -> ShareResourceZippedResponseDTO:
        if shared_entity_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise Exception(f"Entity type {shared_entity_link.entity_type} is not supported")

        zipped_resource: ResourceModel = cls._zip_resource(
            shared_entity_link.entity_id, shared_entity_link.created_by
        )

        # generate the link to download the zipped resource
        download_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/resource/{shared_entity_link.token}/download"
        )
        return ShareResourceZippedResponseDTO(
            version=cls.VERSION,
            entity_type=shared_entity_link.entity_type,
            entity_id=shared_entity_link.entity_id,
            zipped_entity_resource_id=zipped_resource.id,
            download_entity_route=download_url,
        )

    @classmethod
    def _zip_resource(cls, resource_model_id: str, shared_by: User) -> ResourceModel:
        with AuthenticateUser(shared_by):
            return cls.run_zip_resource_scenario(resource_model_id, shared_by)

    @classmethod
    def _create_system_tag(cls, key: str, value: str) -> Tag:
        """Create a tag with system origin."""
        origins = TagOrigins(TagOriginType.SYSTEM, User.get_and_check_sysuser().id)
        return Tag(key, value, origins=origins)

    @classmethod
    def _find_existing_zipped_resource(cls, resource_model_id: str) -> ResourceModel | None:
        """Search for an existing successful zip scenario for the given resource
        and current task version, and return the zipped resource output."""
        search_builder = ScenarioSearchBuilder()
        search_builder.add_tag_filter(
            cls._create_system_tag(cls.TAG_KEY_ZIP_SCENARIO, cls.TAG_KEY_ZIP_SCENARIO_VALUE)
        )
        search_builder.add_tag_filter(
            cls._create_system_tag(cls.TAG_KEY_ZIP_RESOURCE_ID, resource_model_id)
        )
        search_builder.add_tag_filter(
            cls._create_system_tag(cls.TAG_KEY_ZIP_TASK_VERSION, ResourceZipperTask.VERSION)
        )
        search_builder.add_status_filter(ScenarioStatus.SUCCESS)

        scenario = search_builder.search_first()

        if scenario:
            scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
            protocol = scenario_proxy.get_protocol()
            output_task = protocol.get_process("output")
            return output_task.get_input_resource_model(OutputTask.input_name)

        return None

    @classmethod
    def run_zip_resource_scenario(cls, id_: str, shared_by: User) -> ResourceModel:
        """Method that zip a resource and return the new resource.
        If a successful zip scenario already exists for this resource and task version, reuse it.
        """

        # Check if a zip scenario already exists for this resource
        existing_zipped_resource = cls._find_existing_zipped_resource(id_)
        if existing_zipped_resource:
            Logger.info(
                f"Resource {id_} was already zipped to resource {existing_zipped_resource.id}, reusing the output."
            )
            return existing_zipped_resource

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(id_)

        scenario: ScenarioProxy = ScenarioProxy(None, title=f"{resource_model.name} zipper")
        protocol: ProtocolProxy = scenario.get_protocol()

        # Tag the scenario for later lookup
        scenario.add_tags(
            [
                cls._create_system_tag(cls.TAG_KEY_ZIP_SCENARIO, cls.TAG_KEY_ZIP_SCENARIO_VALUE),
                cls._create_system_tag(cls.TAG_KEY_ZIP_RESOURCE_ID, id_),
                cls._create_system_tag(cls.TAG_KEY_ZIP_TASK_VERSION, ResourceZipperTask.VERSION),
            ]
        )

        # Add the importer and the connector
        zipper: ProcessProxy = protocol.add_process(
            ResourceZipperTask, "zipper", {"shared_by_id": shared_by.id}
        )

        # Add source and connect it
        protocol.add_resource("source", resource_model.id, zipper << ResourceZipperTask.input_name)

        # Add output task and connect it
        output_task = protocol.add_output("output", zipper >> ResourceZipperTask.output_name, False)

        scenario.run(auto_delete_if_error=True)
        output_task.refresh()

        return output_task.get_input_resource_model(OutputTask.input_name)

    @classmethod
    def download_zipped_resource(cls, shared_entity_link: ShareLink) -> str:
        """Method that is used to download the zipped resource generated by the shared action"""

        if shared_entity_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise Exception(f"Entity type {shared_entity_link.entity_type} is not supported")

        zipped_resource = cls._find_existing_zipped_resource(shared_entity_link.entity_id)

        if not zipped_resource:
            raise Exception("The resource was not zipped")

        # retrieve the zipped resource that contains the shared entity
        zip_file: Resource = zipped_resource.get_resource()

        if not isinstance(zip_file, File):
            raise Exception("Zip file is not a file")

        # check that the generated zip resource was generated from the shared entity of the token
        if zip_file.get_technical_info("origin_entity_id").value != shared_entity_link.entity_id:
            raise Exception("Zip file does not contain the shared entity")

        return zip_file.path

    @classmethod
    def call_resource_view(
        cls, shared_entity_link: ShareLink, view_name: str, call_view_params: CallViewParams
    ) -> CallViewResult:
        """Method to call a view on a resource"""
        if shared_entity_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise Exception(f"Entity type {shared_entity_link.entity_type} is not supported")

        view_result = ResourceService.get_and_call_view_on_resource_model(
            shared_entity_link.entity_id,
            view_name,
            call_view_params.values,
            call_view_params.save_view_config,
        )

        # If this is a StreamlitResource, send app statistics to the Community
        if shared_entity_link.entity_type is ShareLinkEntityType.RESOURCE:
            resource = cast(
                ResourceModel,
                shared_entity_link.get_model_and_check(
                    shared_entity_link.entity_id, shared_entity_link.entity_type
                ),
            ).get_resource()

            if isinstance(resource, AppResource):
                cls._init_send_resource_app_stat_to_community_thread(
                    app_url=shared_entity_link.get_public_link()
                )

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
    def get_scenario_entity_object_info(
        cls, shared_entity_link: ShareLink
    ) -> ShareScenarioInfoReponseDTO:
        scenario = ScenarioService.get_by_id_and_check(shared_entity_link.entity_id)

        if scenario.is_running:
            raise Exception(
                "The scenario is running and downloaded, please wait for the end of the scenario"
            )

        # generate the link to download the zipped resource
        download_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/scenario/{shared_entity_link.token}/resource/[RESOURCE_ID]/zip"
        )
        return ShareScenarioInfoReponseDTO(
            version=cls.VERSION,
            entity_type=shared_entity_link.entity_type,
            entity_id=shared_entity_link.entity_id,
            entity_object=ScenarioService.export_scenario(shared_entity_link.entity_id),
            resource_route=download_url,
            token=shared_entity_link.token,
            origin=ExternalLabApiService.get_current_lab_info(shared_entity_link.created_by),
        )

    @classmethod
    def zip_shared_scenario_resource(
        cls, shared_entity_link: ShareLink, resource_id: str
    ) -> ShareResourceZippedResponseDTO:
        if shared_entity_link.entity_type != ShareLinkEntityType.SCENARIO:
            raise Exception(f"Entity type {shared_entity_link.entity_type} is not supported")

        cls._check_resource_is_in_scenario(shared_entity_link.entity_id, resource_id)

        zipped_resource: ResourceModel = cls._zip_resource(
            resource_id, shared_entity_link.created_by
        )

        # generate the link to download the zipped resource
        download_url: str = ExternalLabApiService.get_current_lab_route(
            f"share/scenario/{shared_entity_link.token}/resource/{resource_id}/download"
        )
        return ShareResourceZippedResponseDTO(
            version=cls.VERSION,
            entity_type=shared_entity_link.entity_type,
            entity_id=shared_entity_link.entity_id,
            zipped_entity_resource_id=zipped_resource.id,
            download_entity_route=download_url,
        )

    @classmethod
    def download_scenario_resource(cls, shared_entity_link: ShareLink, resource_id: str) -> str:
        """Method that is used to download the zipped resource generated by the shared action"""

        if shared_entity_link.entity_type != ShareLinkEntityType.SCENARIO:
            raise Exception(f"Entity type {shared_entity_link.entity_type} is not supported")

        cls._check_resource_is_in_scenario(shared_entity_link.entity_id, resource_id)

        # retrieve the zipped resource from the zip scenario
        zipped_resource = cls._find_existing_zipped_resource(resource_id)

        if not zipped_resource:
            raise Exception("The resource was not zipped")

        zip_file: Resource = zipped_resource.get_resource()

        if not isinstance(zip_file, File):
            raise Exception("Zip file is not a file")

        return zip_file.path

    @classmethod
    def _check_resource_is_in_scenario(cls, scenario_id: str, resource_id: str) -> None:
        # check that the resource was generated by the scenario or used as input of the scenario

        scenario = ScenarioService.get_by_id_and_check(scenario_id)
        scenario_navigator = EntityNavigatorScenario(scenario)

        if scenario_navigator.get_next_resources().get_as_nav_set().has_entity(
            resource_id
        ) or scenario_navigator.get_previous_resources().get_as_nav_set().has_entity(resource_id):
            return

        raise UnauthorizedException(
            f"The resource {resource_id} was not generated by the shared scenario"
        )
