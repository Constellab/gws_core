# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from gws_core.config.config_params import ConfigParams
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.view.scatterplot_2d_view import ScatterPlot2DView
from gws_core.resource.view.view_types import ViewType


class VulcanoPlotView(ScatterPlot2DView):
    """Vulcano plot view

    Provide the x_threshold and y_threshold to display the threshold lines.

    :param ScatterPlot2DView: _description_
    :type ScatterPlot2DView: _type_
    :raises BadRequestException: _description_
    :raises BadRequestException: _description_
    :return: _description_
    :rtype: _type_
    """

    x_threshold: float = None
    y_threshold: float = None
    _type: ViewType = ViewType.VULCANO_PLOT

    def __init__(self, x_threshold: float = None,
                 y_threshold: float = None):
        super().__init__()
        self.x_threshold = x_threshold
        self.y_threshold = y_threshold

    def add_series(self, x: List[float], y: List[float], name: str = None,
                   x_name: str = None, y_name: str = None, tags: List[Dict[str, str]] = None):
        if self._series and len(self._series) > 0:
            raise BadRequestException("Only one series is allowed")

        if x is None:
            raise BadRequestException("x data is required")

        return super().add_series(x, y, name, x_name, y_name, tags)

    def set_serie(self, x: List[float], y: List[float], name: str = None,
                  x_name: str = None, y_name: str = None, tags: List[Dict[str, str]] = None):
        self._series = []
        return self.add_series(x, y, name, x_name, y_name, tags)

    def data_to_dict(self, params: ConfigParams) -> dict:
        json_ = super().data_to_dict(params)
        json_["x_threshold"] = self.x_threshold
        json_["y_threshold"] = self.y_threshold
        return json_
