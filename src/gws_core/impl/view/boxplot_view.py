# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ...config.config_types import ConfigParams
from ...resource.view import View


class BoxPlotView(View):
    """
    BoxPlotView

    Base class for creating box plots.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "max": List[Float],
                        "q1": List[Float],
                        "median": List[Float],
                        "min": List[Float],
                        "q3": List[Float],
                        "lower_whisker": List[Float],
                        "upper_whisker": List[Float],
                    }
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
    _type: str = "box-plot-view"

    def add_series(
            self,
            x: List[float],
            median: List[float],
            q1: List[float],
            q3: List[float],
            min: List[float],
            max: List[float],
            lower_whisker: List[float],
            upper_whisker: List[float],
            names: List[float] = None):

        if not self._series:
            self._series = []
        self._series.append({
            "data": {
                "x": x,
                "median": median,
                "q1": q1,
                "q3": q3,
                "min": min,
                "max": max,
                "lower_whisker": lower_whisker,
                "upper_whisker": upper_whisker
            },
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