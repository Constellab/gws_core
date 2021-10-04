

from typing import List

from pandas import DataFrame

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
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
        "title": str,
        "subtitle": str,
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

    def to_dict(
            self, x_column_name: str, y_column_name: str, z_column_names: List[str],
            title: str = None, subtitle: str = None) -> dict:
        series = []
        for z_column_name in z_column_names:
            series.append({
                "data": {
                    "x": self._data[x_column_name].values.tolist(),
                    "y": self._data[y_column_name].values.tolist(),
                    "z": self._data[z_column_name].values.tolist(),
                },
                "x_label": x_column_name,
                "y_label": y_column_name,
                "z_label": z_column_name,
            })

        return {
            "type": self._type,
            "title": title,
            "subtitle": subtitle,
            "series": series
        }
