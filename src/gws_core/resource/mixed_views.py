# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, TypedDict

from gws_core.resource.multi_views import MultiViews

from ..config.config_types import ConfigParams, ConfigParamsDict
from ..config.param_spec_helper import ParamSpecHelper
from .view import View


class MixedViews(View):
    """Class MixedViews. This is use to multiple view in a simple plot

    The view model is:
    ```
    {
        "type": "mixed-view"
        "data":
            "views": [
                ...
            ],
    }
    ```
    """

    _sub_views: List[View]
    _type = "mixed-view"
    _allowed_view_types = []

    def __init__(self):
        """[summary]
        """
        super().__init__()
        self._sub_views = []

    def add_view(self, view: View, params: ConfigParamsDict = None) -> None:
        """Add a view to the multi view

        :param view: view
        :type view: Dict[str, Any]
        :param params: values for the config of the view
        :type params: Dict[str, Any]
        :raises Exception: [description]
        """

        if not isinstance(view, View):
            raise Exception('[MixedViews] the view input is not a View')

        if isinstance(view, (MultiViews, MixedViews,)):
            raise Exception('[MixedViews] cannot mix MixedViews or MultiViews')

        if not self._allowed_view_types:
            raise Exception('[MixedViews] No view is allowed. Did you specify the allowed_view_types?')

        if not isinstance(view, self._allowed_view_types):
            raise Exception(f'[MixedViews] can only mix {self._allowed_view_types}')

        config_params: ConfigParams = ParamSpecHelper.get_config_params(view._specs, params)

        self._sub_views.append(
            {
                "view": view,
                "config_params": config_params,
            }
        )

    def data_to_dict(self, params: ConfigParams) -> dict:
        views_dict: List[dict] = []
        for sub_view in self._sub_views:
            view_dict = sub_view["view"].to_dict(sub_view["config_params"])
            views_dict.append(view_dict)

        return {
            "views": views_dict
        }
