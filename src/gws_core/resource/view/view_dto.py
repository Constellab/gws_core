

from typing import Any, Dict, List, Optional

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.view.view_types import ViewType
from gws_core.resource.view_config.view_config_dto import ViewConfigDTO


class ResourceViewMetadatalDTO(BaseModelDTO):
    method_name: str
    view_type: ViewType
    human_name: str
    short_description: str
    default_view: bool
    has_config_specs: bool
    config_specs: Dict[str, ParamSpecDTO]
    style: TypingStyle


class ViewDTO(BaseModelDTO):
    type: ViewType
    title: Optional[str]
    technical_info: List[dict]
    data: Any


class CallViewResultDTO(BaseModelDTO):
    view: ViewDTO
    resource_id: Optional[str]
    view_config: Optional[ViewConfigDTO]
    title: str
    view_type: ViewType
    style: TypingStyle


class ViewTypeDTO(BaseModelDTO):
    type: ViewType
    human_name: Optional[str]
    style: TypingStyle
