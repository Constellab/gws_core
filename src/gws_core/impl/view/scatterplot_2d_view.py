# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ...config.config_types import ConfigParams
from ...resource.view import View


class ScatterPlot2DView(View):
    """
    ScatterPlot2DView

    Base class for creating 2d-scatter plots.

    The view model is:
    ------------------
    ```
    {
        "type": "scatter-plot-2d-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                    },
                    "x_name": str,
                    "y_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    x_label: str = None
    y_label: str = None
    x_tick_labels: List[str] = None
    _series: List = None
    _type: str = "scatter-plot-2d-view"

    def add_series(self, x: List[float], y: List[float], x_name: str = None, y_name: str = None):
        if not self._series:
            self._series = []
        self._series.append({
            "data": {
                "x": x,
                "y": y
            },
            "x_name": x_name,
            "y_name": y_name,
        })

    def to_dict(self, params: ConfigParams) -> dict:
        return {
            **super().to_dict(params),
            "data": {
                "x_label": self.x_label,
                "y_label": self.y_label,
                "x_tick_labels": self.x_tick_labels,
                "series": self._series,
            }
        }