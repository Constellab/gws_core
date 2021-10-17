

from typing import List, Any
from pandas import DataFrame

from ....resource.view import ViewSpecs
from ....config.param_spec import IntParam, StrParam, ListParam
from .base_table_view import BaseTableView


class BoxPlotView(BaseTableView):
    """
    BarPlotView

    Show a set of columns as box plots.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot",
        "title": str,
        "subtitle": str,
        "series": [
            {
                "data": {
                    "x": List[Float],
                    "max": List[Float],
                    "q1": List[Float],
                    "median": List[Float],
                    "min": List[Float],
                    "q3": List[Float],
                },
                "x_ticks": List[Float],
                "x_label": str,
                "y_label": str,
            },
            ...
        ]
    }
    ```
    """

    _type: str="box-plot"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, column_names: List[str] = None, x_tick_labels: list = None, 
                    x_label: str = None, y_label: str = None, **kwargs) -> dict:
        if not x_tick_labels:
            x_tick_labels = column_names
        if not column_names:
            n = min(self._data.shape[1], 50)
            column_names = self._data.columns[0:n]
        series = []
        df = self._data[column_names]
        ymin = df.min()
        ymax = df.max()
        quantile = df.quantile(q=[0.25,0.5,0.75])
        series = [{
            "data": {
                "min": ymin.to_list(),
                "q1": quantile.loc[0.25,:].to_list(),
                "median": quantile.loc[0.5,:].to_list(),
                "q3": quantile.loc[0.75,:].to_list(),
                "max": ymax.to_list(),
            },
            "column_names": column_names,
        }]
        return {
            **super().to_dict(**kwargs),
            "series": series,
            "x_tick_labels": x_tick_labels,
            "x_label": x_label,
            "y_label": y_label,
        }