

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

    def to_markdown(self) -> str:
        markdown = f"#### {self.human_name}"

        if self.default_view:
            markdown += " (default view)"
        markdown += "\n"

        if self.short_description:
            markdown += f"**Description:** {self.short_description}\n\n"

        markdown += f"**View type:** {self.view_type}\n\n"

        markdown += "**Config Specs:**\n"
        if self.config_specs:
            for spec in self.config_specs.values():
                markdown += spec.to_markdown() + "\n"
        else:
            markdown += "No config specs.\n"
        return markdown


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
