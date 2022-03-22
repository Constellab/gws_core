# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Optional, Union

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View


class ScatterPlot2DView(View):
    """
    ScatterPlot2DView

    Base class for creating 2d-scatter plots.

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
        "type": "scatter-plot-2d-view",
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
                        "y": List[Float],
                        "tags": List[Dict[str,str]] | None
                    },
                    "name": str,
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
    _title: str = "2D-Scatter Plot"

    def add_series(
            self, *, x: List[float], y: List[float], name: str = None,
            x_name: str = None, y_name: str = None, tags: List[Dict[str, str]] = None):
        """
        Add a series of points to plot

        :params x: The x-axis positions of points
        :type x: list of float
        :params y: The y-axis magnitudes of points
        :type y: list of float
        :params name: [optional] The name of the serie
        :type name: str
        :params x_name: [optional] The name of x-axis data
        :type x_name: str
        :params y_name: [optional] The name of y-axis data
        :type y_name: str
        :params tags: [optional] The list of `tags` of points. The length of `tags` must be equal to the number of columns in `x`
        :type tags: List[Dict[str, str]]
        """

        if not self._series:
            self._series = []
        if not isinstance(y, list):
            raise BadRequestException("The y-data is required and must be a list of float")

        if x is None:
            x = list(range(0, len(y)))
        else:
            # Convert y to float
            x = self.list_to_float(x)

        # Convert y to float
        y = self.list_to_float(y)

        if tags is not None:
            if not isinstance(tags, list) or len(tags) != len(x):
                raise BadRequestException("The tags must be a list of length equal to the length of x")
            tags = [{str(k): str(v) for k, v in t.items()} for t in tags]
        self._series.append({
            "data": {
                "x": x,
                "y": y,
                "tags": tags
            },
            "name": name,
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
