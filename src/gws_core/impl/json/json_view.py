

from typing import Any, Dict

from gws_core.core.utils.json_helper import JSONHelper
from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...resource.view.view import View


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
    _json_data: Any

    def __init__(self, data: Dict = None):
        super().__init__()
        self.set_data(data)

    def set_data(self, data: Dict):
        if data is None:
            data = {}
        if not isinstance(data, (dict, list, bool, str, int, float)):
            raise BadRequestException("The data must be a json (dictionary, list of primitive or primitive object)")
        self._json_data = JSONHelper.convert_dict_to_json(data)

    def data_to_dict(self, params: ConfigParams = None) -> dict:
        return self._json_data
