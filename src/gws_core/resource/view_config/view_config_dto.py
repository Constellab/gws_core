from typing import Optional

from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_dto import ResourceSimpleDTO
from gws_core.resource.view.view_types import ViewType
from gws_core.scenario.scenario_dto import ScenarioSimpleDTO


class ViewConfigDTO(ModelWithUserDTO):
    title: str
    view_type: ViewType
    view_name: str
    is_favorite: bool
    config_values: dict
    scenario: Optional[ScenarioSimpleDTO]
    resource: Optional[ResourceSimpleDTO]
    style: TypingStyle
