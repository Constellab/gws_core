# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import numpy
from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, ListParam, ParamSet, StrParam
from ....resource.view_types import ViewSpecs
from ...view.boxplot_view import BoxPlotView
from .base_table_view import BaseTableView

MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 999


class TableBoxPlotView(BaseTableView):
    """
    TableBarPlotView

    Class for creating box plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "max": List[Float],
                        "q1": List[Float],
                        "median": List[Float],
                        "min": List[Float],
                        "q3": List[Float],
                        "lower_whisker": List[Float],
                        "upper_whisker": List[Float],
                    }
                },
                ...
            ]
        }
    }
    ```

    See also BoxPlotView
    """

    _type: str = "box-plot-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ParamSet(
            {
                "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
                "use_regexp": BoolParam(default_value=False, human_name="Use regexp", short_description="True to use regular expression for column names; False otherwise"),
            },
            human_name="Column series",
            short_description="Select a series of columns to aggregate as box-plot",
            max_number_of_occurrences=5
        ),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks. By default, the 'column_names' are used"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._data
        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")
        x_tick_labels = params.get_value("x_tick_labels", None)

        # continue ...
        view = BoxPlotView()
        view.x_label = x_label
        view.y_label = y_label

        for param_series in params.get_value("series", []):
            column_names = param_series["column_names"]
            if not column_names:
                n = min(data.shape[1], MAX_NUMBERS_OF_COLUMNS_PER_PAGE)
                column_names = data.columns[0:n].to_list()
                # column_names = data.columns.to_list()
            else:
                if param_series["use_regexp"]:
                    reg = "|".join(["^"+val+"$" for val in column_names])
                    column_names = data.filter(regex=reg).columns.to_list()
                else:
                    column_names = [col for col in column_names if col in data.columns]

            data = data[column_names]

            if not len(column_names):
                continue

            if not x_tick_labels:
                x_tick_labels = column_names

            ymin = data.min(skipna=True).to_list()
            ymax = data.max(skipna=True).to_list()

            quantile = numpy.nanquantile(data.to_numpy(), q=[0.25, 0.5, 0.75], axis=0)
            median = quantile[1, :].tolist()
            q1 = quantile[0, :]
            q3 = quantile[2, :]
            iqr = q3 - q1
            lower_whisker = q1 - (1.5 * iqr)
            upper_whisker = q3 + (1.5 * iqr)
            x = list(range(0, len(column_names)))
            view.add_series(
                x=x,
                median=median,
                q1=q1.tolist(), q3=q3.tolist(), min=ymin, max=ymax,
                lower_whisker=lower_whisker.tolist(), upper_whisker=upper_whisker.tolist()
            )

        x_tick_labels = params.get_value("x_tick_labels", x_tick_labels)
        view.x_tick_labels = x_tick_labels
        return view.to_dict(params)
