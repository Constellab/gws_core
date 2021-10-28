

from typing import Dict

from ..config.config_types import ConfigParams
from ..resource.view import View


class AnyView(View):
    """Special view that return the dict provided in the constructor
    """

    _view_json: Dict

    def __init__(self, view_json: Dict):
        super().__init__(view_json.get("data"))
        self._type = view_json.get("type")
        self._view_json = view_json

    def to_dict(self, config: ConfigParams) -> dict:
        return self._view_json
