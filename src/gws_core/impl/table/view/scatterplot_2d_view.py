# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....resource.view import ViewSpecs
from .base_table_view import BaseTableView


class ScatterPlot2DView(BaseTableView):
    """
    ScatterPlot2DView

    Show a set of columns as 2d-scatter plots.

    The view model is:
    ------------------
    ```
    {
        "type": "scatter-plot-2d-view",
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
                    "x_column_name": str,
                    "y_column_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "scatter-plot-2d-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "x_column_name": StrParam(human_name="X-column name", optional=True, default_value=None, short_description="The column to use as x-axis"),
        "y_column_names": ListParam(human_name="Y-column names", optional=True, default_value=None, short_description="List of columns to use as y-axis"),
        "x_label": StrParam(human_name="X-label", optional=True, default_value=None, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, default_value=None, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        x_column_name = params.get_value("x_column_name", self._data.columns[0])
        y_column_names = params.get_value("y_column_names", [self._data.columns[1]])
        x_label = params.get_value("x_label", x_column_name)
        y_label = params.get_value("y_label", "")

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
            **super().to_dict(params),
            "data": {
                "x_label": x_label,
                "y_label": y_label,
                "x_tick_labels": None,
                "series": series,
            }
        }
