

from typing import Any, List

from pandas import DataFrame

from ....resource.view import ViewSpecs
from ....config.param_spec import IntParam, StrParam, ListParam
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
                "x_column_name": str,
                "y_column_name": str,
                "z_column_name": str,
            },
            ...
        ],
        "x_label": str,
        "y_label": str,
        "z_label": str,
    }
    ```
    """

    _type: str = "scatter-plot-3d"
    _data: DataFrame
    _specs: ViewSpecs = {
        "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
        "y_column_name": StrParam(human_name="Y-column name", short_description="The column to use as y-axis"),
        "z_column_names": ListParam(human_name="Z-column names", short_description="List of columns to use as z-axis"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "z_label": StrParam(human_name="Z-label", optional=True, visibility='protected', short_description="The z-axis label to display"),
    }

    def to_dict(self, x_column_name: str, y_column_name: str, z_column_names: List[str], 
                    x_label: str = None, y_label: str = None, z_label: str = None, **kwargs) -> dict:
        if not x_label:
            x_label = x_column_name

        if not y_label:
            y_label = y_column_name

        series = []
        for z_column_name in z_column_names:
            series.append({
                "data": {
                    "x": self._data[x_column_name].values.tolist(),
                    "y": self._data[y_column_name].values.tolist(),
                    "z": self._data[z_column_name].values.tolist(),
                },
                "x_column_name": x_column_name,
                "y_column_name": y_column_name,
                "z_column_name": z_column_name,
            })

        return {
            **super().to_dict(**kwargs),
            "series": series,
            "x_label": x_label,
            "y_label": y_label,
            "z_label": z_label,
        }
