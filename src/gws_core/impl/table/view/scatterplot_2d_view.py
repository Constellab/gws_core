

from typing import Any, List

from pandas import DataFrame

from ....resource.view import ViewSpecs
from ....config.param_spec import IntParam, StrParam, ListParam

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
                "x_column_name": str,
                "y_column_name": str,
            },
            ...
        ],
        "x_label": str,
        "y_label": str,
    }
    ```
    """

    _type: str = "scatter-plot-2d"
    _data: DataFrame
    _specs: ViewSpecs = {
        "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
        "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis"),
        "x_label": StrParam(human_name="X-label", optional=True, default_value=None, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, default_value=None, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, x_column_name: str, y_column_names: List[str], x_label: str = None, y_label: str = None, **kwargs) -> dict:
        if not x_label:
            x_label = x_column_name

        series = []
        for y_column_name in y_column_names:
            series.append({
                "data": {
                    "x": self._data[x_column_name].values.tolist(),
                    "y": self._data[y_column_name].values.tolist(),
                },
                "x_column_name": x_column_name,
                "y_column_name": y_column_name,
            })
        return {
            **super().to_dict(**kwargs),
            "series": series,
            "x_label": x_label,
            "y_label": y_label,
        }
