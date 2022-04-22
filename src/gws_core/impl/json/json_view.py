# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict

from gws_core.resource.view_types import ViewType

from ...config.config_types import ConfigParams
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...resource.view import View


class JSONView(View):
    """
    Class json view.

    The view model is:
    ```
    {
        "type": "json-view"
        "data": dict
    }
    ```
    """
    _type: ViewType = ViewType.JSON
    _data: Any

    def __init__(self, data: Dict = None):
        super().__init__()
        self.set_data(data)

    def set_data(self, data: Dict):
        if data is None:
            data = {}
        if not isinstance(data, (dict, list, bool, str, int, float)):
            raise BadRequestException("The data must be a json (dictionary, list of primitive or primitive object)")
        self._data = data

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return self._data
