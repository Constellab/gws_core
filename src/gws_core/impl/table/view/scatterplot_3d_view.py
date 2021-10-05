

from typing import Any, List

from pandas import DataFrame

from .base_table_view import BaseTableView


class ScatterPlot3DView(BaseTableView):
    """
    ScatterPlot3DView

    Show a set of columns as 3d-scatter plots.

    The view model is:
    ------------------
    ```
    {
        "type": "line-3d-plot",
        "series": [
            {
                "data": {
                    "x": List[Float],
                    "y": List[Float],
                    "z": List[Float]
                },
                "x_label": str,
                "y_label": str,
                "z_label": str
            },
            ...
        ]
    }
    ```
    """

    _type: str = "scatter-plot-3d"
    _data: DataFrame

    x_column_name: str
    y_column_name: str
    z_column_names: List[str]

    def __init__(self, data: Any, x_column_name: str, y_column_name: str, z_column_names: List[str]):
        super().__init__(data)
        self.x_column_name = x_column_name
        self.y_column_name = y_column_name
        self.z_column_names = z_column_names

    def to_dict(self) -> dict:
        series = []
        for z_column_name in self.z_column_names:
            series.append({
                "data": {
                    "x": self._data[self.x_column_name].values.tolist(),
                    "y": self._data[self.y_column_name].values.tolist(),
                    "z": self._data[z_column_name].values.tolist(),
                },
                "x_label": self.x_column_name,
                "y_label": self.y_column_name,
                "z_label": z_column_name,
            })

        return {
            "type": self._type,
            "series": series
        }
