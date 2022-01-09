# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import numpy

from ...config.config_types import ConfigParams
from ...resource.view import View


class HistogramView(View):
    """
    HistogramView

    Base class for creating histograms.

    The view model is:
    ------------------

    ```
    {
        "type": "histogram-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                    },
                    "name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    x_label: str = None
    y_label: str = None
    nbins: int = 10
    density: bool = False

    x_tick_labels: List[str] = None
    _series: List = None
    _type: str = "histogram-view"
    _title: str = "Histogram"

    def add_series(self, y: List[float], name: str = None):
        if not self._series:
            self._series = []
        self._series.append({
            "y": y,
            "name": name,
        })

    def to_dict(self, params: ConfigParams) -> dict:

        dict_series = []
        for series in self._series:
            y = series["y"]
            name = series["name"]

            hist, bin_edges = numpy.histogram(y, bins=self.nbins, density=self.density)
            bin_centers = (bin_edges[0:-2] + bin_edges[1:-1])/2
            dict_series.append({
                "data": {
                    "x": bin_centers.tolist(),
                    "y": hist.tolist(),
                },
                "name": name,
            })

        return {
            **super().to_dict(params),
            "data": {
                "x_label": self.x_label,
                "y_label": self.y_label,
                "series": dict_series,
            }
        }
