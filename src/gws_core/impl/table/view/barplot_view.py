# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....resource.view_types import ViewSpecs
from .base_table_view import BaseTableView


class BarPlotView(BaseTableView):
    """
    BarPlotView

    Show a set of columns as bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "bar-plot-view",
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
                    "column_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "bar-plot-view"
    _data: DataFrame

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        column_names = params.get_value("column_names", [])
        x_label = params.get_value("x_label", "")
        x_tick_labels = params.get_value("x_tick_labels", self._data.index)
        y_label = params.get_value("y_label", "")

        series = []
        for column_name in column_names:
            series.append({
                "data": {
                    "x": range(0, self._data.shape[0]),
                    "y": self._data[column_name].values.tolist(),
                },
                "column_name": column_name,
            })

        if not series:
            x_tick_labels = None

        return {
            **super().to_dict(params),
            "data": {
                "x_label": x_label,
                "y_label": y_label,
                "x_tick_labels": x_tick_labels,
                "series": series,
            }
        }
