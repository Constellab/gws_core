from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.lab_dto import LabDTO
from gws_core.lab.lab_dto import LabMode
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.scenario.scenario_dto import ScenarioDTO, ScenarioProgressDTO
from gws_core.user.user_dto import UserDTO


class ExternalLabWithUserInfo(BaseModelDTO):
    """Class that contains information about a lab when 2 labs communicate with each other"""

    lab: LabDTO
    lab_api_url: str
    lab_mode: LabMode
    user: UserDTO


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
    scenario_progress: ScenarioProgressDTO | None = None
