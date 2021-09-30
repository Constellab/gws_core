

from typing import List

from pandas import DataFrame

from ...resource.view import View


class Line3DPlotView(View):
    """
    Class for 3D-line plot view

    The view model is:
    ```
    {
        "type": "line-3d-plot",
        "series": [
            {
                "title": str,
                "subtitle": str,
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

    _type: str
    _data: DataFrame

    def __init__(self, data: DataFrame):
        super().__init__(type="line-3d-plot", data=data)

    def to_dict(
            self, x_column_name: str, y_column_name: str, z_column_names: List[str],
            title: str = None, subtitle: str = None) -> dict:
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
