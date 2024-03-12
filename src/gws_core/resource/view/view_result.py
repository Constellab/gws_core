# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from gws_core.model.typing_style import TypingStyle
from gws_core.resource.view.view_dto import CallViewResultDTO, ViewDTO
from gws_core.resource.view.view_types import ViewType
from gws_core.resource.view_config.view_config import ViewConfig


class CallViewResult():
    view: ViewDTO
    resource_id: str
    view_config: Optional[ViewConfig]
    title: str
    view_type: ViewType
    style: Optional[TypingStyle]

    def __init__(self, view: ViewDTO, resource_id: str, view_config: Optional[ViewConfig],
                 title: str, view_type: ViewType, style: Optional[TypingStyle] = None) -> None:
        self.view = view
        self.resource_id = resource_id
        self.view_config = view_config
        self.title = title
        self.view_type = view_type
        self.style = style

    def to_dto(self) -> CallViewResultDTO:
        return CallViewResultDTO(
            view=self.view,
            resource_id=self.resource_id,
            view_config=self.view_config.to_dto() if self.view_config else None,
            title=self.title,
            view_type=self.view_type,
            style=self.style if self.style else self.view_type.get_typing_style()
        )
