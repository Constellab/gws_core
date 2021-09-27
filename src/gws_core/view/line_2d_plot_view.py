

from typing import List
from pandas import DataFrame
from .view import View

class Line2DPlotView(View):
    """
    Class 2D-line plot view

    The 2D-line view model is:

    ```
    {
        "series": [
            {
                "name": "Series 1",
                "data": {
                    "x": List[Float],
                    "y": List[Float]
                }
            },
            {
                "name": "Series 2",
                "data": {
                    "x": List[Float], Int
                    "y": List[Float]
                }
            },
            ...
        ]
    }
    ```
    """

    _data: DataFrame

    def __init__(self, data: DataFrame):
        super().__init__(type="line-2d-plot", data=data)

    def to_dict(self, x_column_name: str, y_column_names: List[str], title: str=None, subtitle: str=None) -> dict:
        series = []
        for y_column_name in y_column_names:
            series.append({
                "tile": title,
                "subtile": subtitle,
                "data": {
                    "x": self._data[x_column_name].values.to_list(),
                    "y": self._data[y_column_name].values.to_list(),
                },
                "x_label": x_column_name,
                "y_label": y_column_name,
            })
        return {
            "type": self._type,
            "series": series
        }