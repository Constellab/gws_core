# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, List

from gws_core.config.config_types import ConfigParams
from gws_core.resource.view import View
from gws_core.resource.view_types import ViewType

from ...core.classes.jsonable import ListJsonable

if TYPE_CHECKING:
    from gws_core.resource.resource_model import ResourceModel


class ResourcesListView(View):
    """View that list resources with a link to them

    :param View: _description_
    :type View: _type_

    {
        "type": "resources-list-view",
        "title": str,
        "caption": str,
        "data": List[{}]
    }
    """

    _resource_model: List[ResourceModel]
    _type: ViewType = ViewType.RESOURCES_LIST_VIEW
    _title: str = "Resources list"

    def __init__(self):
        super().__init__()
        self._resource_model = []

    def add_resource(self, resource_model: ResourceModel) -> None:
        self._resource_model.append(resource_model)

    def add_resources(self, resource_model_json: List[ResourceModel]) -> None:
        self._resource_model += resource_model_json

    def to_dict(self, params: ConfigParams) -> dict:

        return {
            **super().to_dict(params),
            "data": ListJsonable(self._resource_model).to_json()
        }
