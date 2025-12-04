from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.scenario.scenario_dto import ScenarioDTO, ScenarioProgressDTO


class ExternalLabWithUserInfo(BaseModelDTO):
    """Class that contains information a lab when 2 labs communicate with each other"""

    lab_id: str
    lab_name: str
    lab_api_url: str

    user_id: str
    user_firstname: str
    user_lastname: str

    space_id: Optional[str]
    space_name: Optional[str]


class ExternalLabImportRequestDTO(BaseModelDTO):
    params: dict


class ExternalLabImportResourceResponseDTO(BaseModelDTO):
    resource_model: ResourceModelDTO
    resource_url: str
    lab_info: ExternalLabWithUserInfo


class ExternalLabImportScenarioResponseDTO(BaseModelDTO):
    scenario: ScenarioDTO
    scenario_url: str
    lab_info: ExternalLabWithUserInfo
    scenario_progress: Optional[ScenarioProgressDTO] = None
