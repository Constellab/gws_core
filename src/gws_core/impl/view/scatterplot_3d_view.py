# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ...config.config_types import ConfigParams
from ...resource.view import View


class ScatterPlot3DView(View):
    """
    ScatterPlot3DView

    Base class for creating 3d-scatter plots.

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
                        "z": List[Float]
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
    _type: str = "scatter-plot-3d-view"
    _title: str = "3D-Scatter Plot"

    def add_series(
            self, x: List[float],
            y: List[float],
            z: List[float],
            x_name: str = None, y_name: str = None, z_name: str = None):
        if not self._series:
            self._series = []
        self._series.append({
            "data": {
                "x": x,
                "y": y,
                "z": z
            },
            "x_name": x_name,
            "y_name": y_name,
            "z_name": z_name
        })

    def to_dict(self, params: ConfigParams) -> dict:
        return {
            **super().to_dict(params),
            "data": {
                "x_label": self.x_label,
                "y_label": self.y_label,
                "z_label": self.z_label,
                "x_tick_labels": self.x_tick_labels,
                "y_tick_labels": self.y_tick_labels,
                "series": self._series,
            }
        }
