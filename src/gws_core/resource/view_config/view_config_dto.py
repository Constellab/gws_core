

from typing import Optional

from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.experiment.experiment_dto import ExperimentSimpleDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_dto import ResourceSimpleDTO
from gws_core.resource.view.view_types import ViewType


class ViewConfigDTO(ModelWithUserDTO):
    title: str
    view_type: ViewType
    view_name: str
    is_favorite: bool
    config_values: dict
    experiment: Optional[ExperimentSimpleDTO]
    resource: Optional[ResourceSimpleDTO]
    style: TypingStyle
