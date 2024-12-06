

from typing import Dict

from gws_core.config.config_types import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.process.process_proxy import ProcessProxy
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.task.resource_downloader_http import \
    ResourceDownloaderHttp
from gws_core.resource.task.send_resource_to_lab import SendResourceToLab
from gws_core.scenario.scenario_proxy import ScenarioProxy
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
