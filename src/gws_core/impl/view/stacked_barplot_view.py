# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Union

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.resource.view_types import ViewType
from pandas import DataFrame

from ...config.config_types import ConfigParams
from .barplot_view import BarPlotView


class StackedBarPlotView(BarPlotView):
    """
    StackedBarPlotView

    Base class for creating stacked-bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "stacked-bar-plot-view",
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
                },
                ...
            ]
        }
    }
    ```

    See also BarPlotView
    """

    _type: ViewType = ViewType.STACKED_BAR_PLOT
    _title: str = "Stacked-Bar Plot"
    _normalize: bool = False
    _series_sums: DataFrame = None

    def __init__(self, normalize: bool = False):
        super().__init__()
        self._normalize = normalize

    def add_series(self, x: Union[List[float], List[str], ] = None, y: List[float] = None, name: str = None,
                   tags: List[Dict[str, str]] = None):
        """
        Add a series of stacked-bars to plot

        :params x: The x-axis positions of bars
        :type x: list of float
        :params y: The y-axis magnitudes of bars
        :type y: list of float
        :params name: The name of the series
        :type name: str
        :params tags: [optional] The list of `tags`. The length of `tags` must be equal to the number of columns in `x`
        :type tags: List[Dict[str, str]]
        """

        if self._normalize:
            y = NumericHelper.list_to_float(y, default_value=0)
            if self._series_sums is None:
                self._series_sums = DataFrame(y)
            else:
                self._series_sums = self._series_sums + DataFrame(y)

        super().add_series(x=x, y=y, name=name, tags=tags)

    def to_dict(self, params: ConfigParams) -> dict:
        view_dict = super().to_dict(params)
        if self._normalize:
            for i, _ in enumerate(view_dict["data"]["series"]):
                df = view_dict["data"]["series"][i]["data"]["y"]
                df = DataFrame(df) / self._series_sums
                view_dict["data"]["series"][i]["data"]["y"] = df.iloc[:, 0].values.tolist()

        return view_dict
