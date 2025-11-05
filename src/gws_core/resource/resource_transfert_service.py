

from typing import Dict

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.process.process_proxy import ProcessProxy
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_dto import ShareResourceWithSpaceRequestDTO
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.task.resource_downloader_http import \
    ResourceDownloaderHttp
from gws_core.resource.task.send_resource_to_lab import SendResourceToLab
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import (GenerateShareLinkDTO,
                                       ShareLinkEntityType, ShareLinkType)
from gws_core.space.space_dto import ShareResourceWithSpaceDTO
from gws_core.space.space_service import SpaceService
from gws_core.task.plug.output_task import OutputTask

from .resource_model import ResourceModel


class ResourceTransfertService():

    @classmethod
    def import_resource_from_link_sync(cls, values: ConfigParamsDict) -> ResourceModel:
        """ Run the import resource synchronously and return the imported resource
        """

        scenario = cls._build_import_resource_from_link_scenario(values)

        scenario.run()

        # return the resource model of the output process
        output_task = scenario.get_protocol().get_process('output').refresh()
        return output_task.get_input_resource_model(OutputTask.input_name)

    @classmethod
    def import_resource_from_link_async(cls, values: ConfigParamsDict) -> Scenario:
        """ Run the import resource asynchronously, return the running import scenario
        """

        scenario = cls._build_import_resource_from_link_scenario(values)
        scenario.run_async()
        return scenario.get_model().refresh()

    @classmethod
    def _build_import_resource_from_link_scenario(cls, values: ConfigParamsDict) -> ScenarioProxy:

        link: str = values.get(ResourceDownloaderHttp.LINK_PARAM_NAME)
        file_name = link.split('/')[-1]
        # Create an resource containing 1 resource downloader , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(title=f"Download {file_name}")
        protocol: ProtocolProxy = scenario.get_protocol()

        # Add the importer and the connector
        downloader: ProcessProxy = protocol.add_process(ResourceDownloaderHttp, 'downloader', values)

        # Add output and connect it
        protocol.add_output('output', downloader >> ResourceDownloaderHttp.OUTPUT_NAME)

        return scenario

    @classmethod
    def get_imported_resource_from_scenario(cls, scenario_id: str) -> ResourceModel:
        """Get the imported resource from the scenario
        """
        scenario_proxy = ScenarioProxy.from_existing_scenario(scenario_id)
        if not scenario_proxy.is_success():
            raise Exception("The scenario is not finished or not successful, can't retrieve the resource")
        output_task = scenario_proxy.get_protocol().get_process('output')
        return output_task.get_input_resource_model(OutputTask.input_name)

    @classmethod
    def get_import_from_link_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return ResourceDownloaderHttp.config_specs.to_dto()

    @classmethod
    def export_resource_to_lab(cls, resource_id: str, values: ConfigParamsDict) -> Scenario:

        # Create an resource containing 1 resource downloader , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(title="Send resource")
        protocol = scenario.get_protocol()

        # Add the importer and the connector
        send_process = protocol.add_process(SendResourceToLab, 'sender', values)

        # add input resource
        protocol.add_resource('resource', resource_id, send_process.get_input_port(SendResourceToLab.INPUT_NAME))

        scenario.run()

        return scenario.get_model().refresh()

    @classmethod
    def get_export_resource_to_lab_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return SendResourceToLab.config_specs.to_dto()

    @classmethod
    @GwsCoreDbManager.transaction()
    def share_resource_with_space(cls, resource_id: str, request_dto: ShareResourceWithSpaceRequestDTO) -> ShareLink:

        resource_model = ResourceService.get_by_id_and_check(resource_id)

        # create or get the share link without expiration date
        share_dto = GenerateShareLinkDTO(
            entity_id=resource_id,
            entity_type=ShareLinkEntityType.RESOURCE,
            valid_until=request_dto.valid_until
        )
        share_link = ShareLinkService.get_or_create_valid_share_link(share_dto, ShareLinkType.SPACE)

        # share the resource with the space
        resource_dto: ShareResourceWithSpaceDTO = ShareResourceWithSpaceDTO(
            resource_id=resource_model.id,
            name=resource_model.name,
            style=resource_model.style,
            typing_name=resource_model.resource_typing_name,
            token=share_link.token,
            valid_until=share_link.valid_until,
            is_application=resource_model.is_application()
        )

        SpaceService.get_instance().share_resource(request_dto.folder_id, resource_dto)

        return share_link
