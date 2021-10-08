

from typing import Any, List

from pandas import DataFrame

from ....resource.view import View
from .base_table_view import BaseTableView


class ScatterPlot2DView(BaseTableView):
    """
    ScatterPlot2DView

    Show a set of columns as 2d-scatter plots.

    The view model is:
    ------------------
    ```
    {
        "type": "line-2d-plot",
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

    x_column_name: str
    y_column_names: List[str]

    def __init__(self, data: Any, x_column_name: str, y_column_names: List[str]):
        super().__init__(data)
        self.x_column_name = x_column_name
        self.y_column_names = y_column_names

    def to_dict(self) -> dict:
        series = []
        for y_column_name in self.y_column_names:
            series.append({
                "data": {
                    "x": self._data[self.x_column_name].values.tolist(),
                    "y": self._data[y_column_name].values.tolist(),
                },
                "x_label": self.x_column_name,
                "y_label": y_column_name,
            })
        return {
            "type": self._type,
            "data": series
        }
