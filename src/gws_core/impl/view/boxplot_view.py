# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View


class BoxPlotView(View):
    """
    BoxPlotView

    Base class for creating box plots.

    :property x_label: The X-axis label
    :type x_label: str
    :property y_label: The Y-axis label
    :type y_label: str
    :property x_tick_labels: The labels of X-ticks
    :type x_tick_labels: list[str]

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "title": str,
        "caption": str,
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
    _title: str = "Box Plot"

    def add_series(
            self, *,
            x: List[float] = None,
            median: List[float] = None,
            q1: List[float] = None,
            q3: List[float] = None,
            min: List[float] = None,
            max: List[float] = None,
            lower_whisker: List[float] = None,
            upper_whisker: List[float] = None):

        if not self._series:
            self._series = []

        if (median is None) or not isinstance(median, list):
            raise BadRequestException("The median data is required and must be a list of float")
        if (q1 is None) or not isinstance(q1, list):
            raise BadRequestException("The q1 data is required and must be a list of float")
        if (q3 is None) or not isinstance(q3, list):
            raise BadRequestException("The q3 data is required and must be a list of float")
        if (lower_whisker is None) or not isinstance(lower_whisker, list):
            raise BadRequestException("The lower_whisker data is required and must be a list of float")
        if (upper_whisker is None) or not isinstance(upper_whisker, list):
            raise BadRequestException("The upper_whisker data is required and must be a list of float")

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
