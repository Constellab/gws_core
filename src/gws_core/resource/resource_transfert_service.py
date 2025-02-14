

from datetime import timedelta
from typing import Dict

from gws_core.config.config_types import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.decorator.transaction import transaction
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.process.process_proxy import ProcessProxy
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_dto import ShareResourceWithSpaceRequestDTO
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.task.resource_downloader_http import \
    ResourceDownloaderHttp
from gws_core.resource.task.send_resource_to_lab import SendResourceToLab
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import GenerateShareLinkDTO, ShareLinkType
from gws_core.space.space_dto import ShareResourceWithSpaceDTO
from gws_core.space.space_service import SpaceService
from gws_core.task.plug.output_task import OutputTask

from .resource_model import ResourceModel


class ResourceTransfertService():

    @classmethod
    def import_resource_from_link(cls, values: ConfigParamsDict) -> ResourceModel:

        link: str = values.get(ResourceDownloaderHttp.LINK_PARAM_NAME)
        file_name = link.split('/')[-1]
        # Create an resource containing 1 resource downloader , 1 output task
        resource: ScenarioProxy = ScenarioProxy(title=f"Download {file_name}")
        protocol: ProtocolProxy = resource.get_protocol()

        # Add the importer and the connector
        downloader: ProcessProxy = protocol.add_process(ResourceDownloaderHttp, 'downloader', values)

        # Add output and connect it
        output_task = protocol.add_output('output', downloader >> ResourceDownloaderHttp.OUTPUT_NAME)

        resource.run()

        # return the resource model of the output process
        output_task.refresh()
        return output_task.get_input_resource_model(OutputTask.input_name)

    @classmethod
    def get_import_from_link_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return ResourceDownloaderHttp.get_config_specs_dto()

    @classmethod
    def export_resource_to_lab(cls, resource_id: str, values: ConfigParamsDict) -> None:

        # Create an resource containing 1 resource downloader , 1 output task
        resource: ScenarioProxy = ScenarioProxy(title="Send resource")
        protocol = resource.get_protocol()

        # Add the importer and the connector
        send_process = protocol.add_process(SendResourceToLab, 'sender', values)

        # add input resource
        protocol.add_resource('resource', resource_id, send_process.get_input_port(SendResourceToLab.INPUT_NAME))

        resource.run()

    @classmethod
    def get_export_resource_to_lab_config_specs(cls) -> Dict[str, ParamSpecDTO]:
        return SendResourceToLab.get_config_specs_dto()

    @classmethod
    @transaction()
    def share_resource_with_space(cls, resource_id: str, request_dto: ShareResourceWithSpaceRequestDTO) -> None:

        resource_model = ResourceService.get_by_id_and_check(resource_id)

        # create or get the share link without expiration date
        share_dto = GenerateShareLinkDTO(
            entity_id=resource_id,
            entity_type=ShareLinkType.RESOURCE,
            valid_until=request_dto.valid_until
        )
        share_link = ShareLinkService.get_or_create_valid_share_link(share_dto)

        # share the resource with the space
        resource_dto: ShareResourceWithSpaceDTO = ShareResourceWithSpaceDTO(
            resource_id=resource_model.id,
            name=resource_model.name,
            style=resource_model.style,
            typing_name=resource_model.resource_typing_name,
            share_link=share_link.get_preview_link(),
            valid_until=share_link.valid_until
        )

        SpaceService.get_instance().share_resource(request_dto.folder_id, resource_dto)
