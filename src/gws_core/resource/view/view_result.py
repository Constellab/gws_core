# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.resource.view_config.view_config import ViewConfig


class CallViewResult():
    view: Dict
    resource_id: str
    view_config: ViewConfig
    title: str
    view_type: str

    def __init__(self, view: Dict, resource_id: str, view_config: ViewConfig, title: str, view_type: str):
        self.view = view
        self.resource_id = resource_id
        self.view_config = view_config
        self.title = title
        self.view_type = view_type

    def to_dto(self) -> CallViewResultDTO:
        return CallViewResultDTO(
            view=self.view,
            resource_id=self.resource_id,
            view_config=self.view_config.to_dto() if self.view_config else None,
            title=self.title,
            view_type=self.view_type
        )

    def to_json(self):
        return self.to_dto()
