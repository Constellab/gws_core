

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....resource.view import ViewSpecs
from .base_table_view import BaseTableView


class BoxPlotView(BaseTableView):
    """
    BarPlotView

    Show a set of columns as box plots.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "data": [
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

    _type: str = "box-plot-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, config: ConfigParams) -> dict:

        column_names = config.get_value("column_names", [])
        x_tick_labels = config.get_value("x_tick_labels", None)
        x_label = config.get_value("x_label", "")
        y_label = config.get_value("y_label", "")

        if not x_tick_labels:
            x_tick_labels = column_names
        if not column_names:
            n = min(self._data.shape[1], 50)
            column_names = self._data.columns[0:n]

        series = []
        df = self._data[column_names]
        ymin = df.min().to_list()
        ymax = df.max().to_list()

        quantile = df.quantile(q=[0.25, 0.5, 0.75])
        q1s = quantile.loc[0.25, :].to_list()
        medians = quantile.loc[0.50, :].to_list()
        q3s = quantile.loc[0.75, :].to_list()

        series = []

        # Create on serie per column
        for index, column_name in enumerate(column_names):
            q1 = q1s[index]
            q3 = q3s[index]
            inter_quantile_range = q3 - q1
            series.append(
                {
                    "data": {
                        "min": ymin[index],
                        "q1": q1,
                        "median": medians[index],
                        "q3": q3,
                        "max": ymax[index],
                        "lower_whisker": q1 - (1.5 * inter_quantile_range),
                        "upper_whisker": q3 + (1.5 * inter_quantile_range),
                        "nb_of_data": len(self._data[column_name])
                    },
                    "column_name": column_name})
        return {
            **super().to_dict(config),
            "data": series,
            "x_tick_labels": x_tick_labels,
            "x_label": x_label,
            "y_label": y_label,
        }
