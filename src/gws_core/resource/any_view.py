# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from ..config.config_types import ConfigParams
from ..resource.view import View


class AnyView(View):
    """Special view that return the dict provided in the constructor
    """

    _view_json: Dict

    def __init__(self, view_json: Dict):
        super().__init__()
        self._type = view_json.get("type")
        self._view_json = view_json

    def to_dict(self, params: ConfigParams) -> dict:
        return self._view_json
