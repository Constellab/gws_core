

from typing import List
from pandas import DataFrame
from .view import View

class Line3DPlotView(View):
    """
    Class 3D-line plot view

    The 3D-line view model is:

    ```
    {
        "series": [
            {
                "name": "Series 1",
                "data": {
                    "x": List[Float],
                    "y": List[Float],
                    "z": List[Float]
                }
            },
            {
                "name": "Series 2",
                "data": {
                    "x": List[Float], Int
                    "y": List[Float], Int
                    "z": List[Float]
                }
            },
            ...
        ]
    }
    ```
    """

    _type: str
    _data: DataFrame

    def __init__(self, data: DataFrame):
        super().__init__(type="line-3d-plot", data=data)

    def to_dict(self, x_column_name: str, y_column_name: str, z_column_names: List[str], title: str=None, subtitle: str=None) -> dict:
        series = []
        for z_column_name in z_column_names:
            series.append({
                "title": title,
                "subtitle": subtitle,
                "data": {
                    "x": self._data[x_column_name].values.to_list(),
                    "y": self._data[y_column_name].values.to_list(),
                    "z": self._data[z_column_name].values.to_list(),
                },
                "x_label": x_column_name,
                "y_label": y_column_name,
                "z_label": z_column_name,
            })

        return {
            "type": self._type,
            "series": series
        }
