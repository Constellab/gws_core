from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.tag.tag_dto import TagDTO


class ZipScenario(BaseModelDTO):
    id: str
    title: str
    description: Optional[RichTextDTO] = None
    status: ScenarioStatus
    folder: Optional[SpaceFolderDTO] = None
    error_info: Optional[ProcessErrorInfo] = None
    tags: Optional[List[TagDTO]] = None


class ZipScenarioInfo(BaseModelDTO):
    """Content of the info.json file in the zip file when a resource is zipped"""

    zip_version: int
    scenario: ZipScenario
    protocol: ScenarioProtocolDTO
