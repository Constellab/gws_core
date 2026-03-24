from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.process.process_types import ProcessErrorInfo
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.resource.resource_dto import ResourceModelExportDTO
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.tag.tag_dto import TagDTO


class ScenarioExportDTO(BaseModelDTO):
    id: str
    title: str
    description: RichTextDTO | None = None
    status: ScenarioStatus
    folder: SpaceFolderDTO | None = None
    error_info: ProcessErrorInfo | None = None
    tags: list[TagDTO] | None = None


class ScenarioExportPackage(BaseModelDTO):
    """Content of the info.json file in the zip file when a resource is zipped"""

    zip_version: int = 1
    scenario: ScenarioExportDTO
    protocol: ScenarioProtocolDTO
    main_resource_models: list[ResourceModelExportDTO]
