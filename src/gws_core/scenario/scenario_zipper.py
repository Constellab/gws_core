
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.scenario.scenario_enums import ScenarioStatus


class ZipScenario(BaseModelDTO):
    id: str
    title: str
    description: Optional[dict]
    status: ScenarioStatus
    folder: Optional[SpaceFolderDTO]
    error_info: Optional[ProcessErrorInfo]


class ZipScenarioInfo(BaseModelDTO):
    """ Content of the info.json file in the zip file when a resource is zipped"""
    zip_version: int
    scenario: ZipScenario
    protocol: ScenarioProtocolDTO
