
from typing import Any, Dict

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
    _type: str = "json-view"
    _data: Any

    def __init__(self, data: Dict):
        if data is not None and not isinstance(data, (dict, list, bool, str, int, float)):
            raise BadRequestException("The data must be a json (dictionary, list of primitive or primitive object)")
        super().__init__(data=data)

    def to_dict(self, params: ConfigParams = None) -> dict:
        return {
            "type": self._type,
            "data": self._data,
        }
