# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view.view import View


class ScatterPlot3DView(View):
    """
    ScatterPlot3DView

    Base class for creating 3d-scatter plots.

    :property x_label: The X-axis label
    :type x_label: str
    :property y_label: The Y-axis label
    :type y_label: str
    :property z_label: The Z-axis label
    :type z_label: str
    :property x_tick_labels: The labels of X-ticks
    :type x_tick_labels: list[str]
    :property y_tick_labels: The labels of Y-ticks
    :type y_tick_labels: list[str]

    The view model is:
    ------------------
    ```
    {
        "type": "scatter-plot-3d-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "z_label": str,
            "x_tick_labels": List[str] | None,
            "y_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                        "z": List[Float],
                        "tags": List[Dict[str,str]] | None
                    },
                    "x_data": str,
                    "y_data": str,
                    "z_column_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    x_label: str = None
    y_label: str = None
    z_label: str = None
    x_tick_labels: List[str] = None
    y_tick_labels: List[str] = None
    _series: List = None
    _type: ViewType = ViewType.SCATTER_PLOT_3D
    _title: str = "3D-Scatter Plot"

    def add_series(
            self, *,
            x: List[float],
            y: List[float],
            z: List[float],
            x_name: str = None, y_name: str = None, z_name: str = None, tags: List[Dict[str, str]] = None):
        """
        Add a series of points to plot

        :params x: The x-axis positions of points
        :type x: list of float
        :params y: The y-axis positions of points
        :type y: list of float
        :params z: The z-axis magnitudes of points
        :type z: list of float
        :params x_name: [optional] The name of x-axis data
        :type x_name: str
        :params y_name: [optional] The name of y-axis data
        :type y_name: str
        :params z_name: [optional] The name of z-axis data
        :type z_name: str
        :params tags: [optional] The list of `tags` of points. The length of `tags` must be equal to the number of columns in `x`
        :type tags: List[Dict[str, str]]
        """
        if not self._series:
            self._series = []
        if not isinstance(z, list):
            raise BadRequestException("The z-data is required and must be a list of float")

        if y is None:
            y = list(range(0, len(z)))
        else:
            y = [float(val) for val in y]

        if x is None:
            x = list(range(0, len(z)))
        else:
            x = [float(val) for val in x]

        if tags is not None:
            if not isinstance(tags, list) or len(tags) != len(x):
                raise BadRequestException("The tags must a list of length equal to the length of x")
            tags = [{str(k): str(v) for k, v in t.items()} for t in tags]
        self._series.append({
            "data": {
                "x": x,
                "y": y,
                "z": z,
                "tags": tags
            },
            "x_name": x_name,
            "y_name": y_name,
            "z_name": z_name,
        })

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "x_label": self.x_label,
            "y_label": self.y_label,
            "z_label": self.z_label,
            "x_tick_labels": self.x_tick_labels,
            "y_tick_labels": self.y_tick_labels,
            "series": self._series,
        }
