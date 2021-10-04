

from typing import List

from pandas import DataFrame

from ....resource.view import View
from .base_table_view import BaseTableView


class ScatterPlot2DView(BaseTableView):
    """
    ScatterPlot3DView

    Show a set of columns as 2d-scatter plots.

    The view model is:
    ------------------
    ```
    {
        "type": "line-2d-plot",
        "title": str,
        "subtitle": str,
        "series": [
            {
                "data": {
                    "x": List[Float],
                    "y": List[Float]
                },
                "x_label": str,
                "y_label": str,
            },
            ...
        ]
    }
    ```
    """

    _type: str = "scatter-plot-2d"
    _data: DataFrame

    def to_dict(self, x_column_name: str, y_column_names: List[str], title: str = None, subtitle: str = None) -> dict:
        series = []
        for y_column_name in y_column_names:
            series.append({
                "data": {
                    "x": self._data[x_column_name].values.tolist(),
                    "y": self._data[y_column_name].values.tolist(),
                },
                "x_label": x_column_name,
                "y_label": y_column_name,
            })
        return {
            "type": self._type,
            "title": title,
            "subtitle": subtitle,
            "series": series
        }
