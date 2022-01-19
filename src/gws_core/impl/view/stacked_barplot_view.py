# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame
from .barplot_view import BarPlotView
from typing import List, Union
from ...config.config_types import ConfigParams

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

    _type: str = "stacked-bar-plot-view"
    _title: str = "Stacked-Bar Plot"
    normalize = False
    _series_sums: DataFrame = None
    
    def add_series(self, *, x: Union[List[float], List[str], ] = None, y: List[float] = None, name: str = None):
        if self.normalize:
            if self._series_sums is None:
                self._series_sums = DataFrame(y)
            else:
                self._series_sums = self._series_sums + DataFrame(y)

        super().add_series(x=x,y=y,name=name)

    def to_dict(self, params: ConfigParams) -> dict:
        view_dict = super().to_dict(params)
        if self.normalize:
            for i, _ in enumerate(view_dict["data"]["series"]):
                df = view_dict["data"]["series"][i]["data"]["y"]
                df = DataFrame(df) / self._series_sums
                view_dict["data"]["series"][i]["data"]["y"] = df.iloc[:,0].values.tolist()
        
        return view_dict