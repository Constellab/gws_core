
from typing import Any, Dict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ...resource.view import View


class JsonView(View):
    """
    Class json view.

    The view model is:
    ```
    {
        "type": "json-view"
        "title": str
        "subtitle": str
        "data": dict
    }
    ```
    """

    _data: Any

    def __init__(self, data: Dict):
        if not isinstance(data, (dict, list, bool, str, int, float)):
            raise BadRequestException("The data must be a json (dictionary, list of primitive or primitive object)")
        super().__init__(type="json-view", data=data)

    def to_dict(self, title: str = None, subtitle: str = None) -> dict:
        return {
            "type": self._type,
            "title": title,
            "subtile": subtitle,
            "data": self._data,
        }
