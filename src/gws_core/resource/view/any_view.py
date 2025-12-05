
from gws_core.core.utils.string_helper import StringHelper

from ...config.config_params import ConfigParams
from .view import View
from .view_types import ViewType


class AnyView(View):
    """Special view that return the dict provided in the constructor"""

    _view_data_json: dict

    def __init__(self, view_json: dict):
        self._type = StringHelper.to_enum(ViewType, view_json.get("type"))
        self._title = view_json.get("title")
        self._technical_info = view_json.get("technical_info")
        super().__init__()
        self._view_data_json = view_json.get("data")

    def data_to_dict(self, params: ConfigParams) -> dict:
        return self._view_data_json
