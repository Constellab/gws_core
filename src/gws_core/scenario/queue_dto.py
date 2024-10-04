

from gws_core.core.model.model_dto import ModelDTO
from gws_core.scenario.scenario_dto import ScenarioDTO
from gws_core.user.user_dto import UserDTO


class JobDTO(ModelDTO):
    user: UserDTO
    scenario: ScenarioDTO
