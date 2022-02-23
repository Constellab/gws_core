# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, ParamSet, StrParam
from ....resource.view_types import ViewSpecs
from ...view.boxplot_view import BoxPlotView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table


class TableBoxPlotView(BaseTableView):
    """
    TableBarPlotView

    Class for creating box plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str],
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

    DEFAULT_NUMBER_OF_COLUMNS = 3

    _type: str = "box-plot-view"
    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ParamSet(
            {
                "y_data_columns": ListParam(human_name="Set of Y-data columns", short_description="Set of columns to aggregate as a series of box plots"),
            },
            optional=True,
            human_name="Series of data",
            short_description=f"Select series of data. By default the first {DEFAULT_NUMBER_OF_COLUMNS} columns are plotted",
            max_number_of_occurrences=5
        ),
        "x_label": StrParam(human_name="X-axis label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-axis label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "x_tick_labels": ListParam(human_name="X-tick labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks. By default, the 'column_names' are used"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._table.select_numeric_columns().get_data()
        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")
        x_tick_labels = params.get_value("x_tick_labels", [])

        # continue ...
        box_view = BoxPlotView()
        box_view.x_label = x_label
        box_view.y_label = y_label
        box_view.x_tick_labels = x_tick_labels

        series = params.get_value("series", [])
        if not series:
            n = min(self.DEFAULT_NUMBER_OF_COLUMNS, data.shape[1])
            series = [{
                "y_data_columns": data.columns[0:n].values.tolist()
            }]

        for param_series in series:
            y_data_columns = param_series.get("y_data_columns")
            self.check_column_names(y_data_columns)

            selected_table = self._table.select_by_column_names(y_data_columns)

            # create tags using {column_name, colunm_tags}
            extended_col_tags = selected_table.get_column_tags()
            extended_col_tags = [{"name": y_data_columns[i], **t} for i, t in enumerate(extended_col_tags)]

            box_view.add_data(
                data=selected_table.get_data(),  # data[y_data_columns],
                tags=extended_col_tags
            )

        # if possible, try to use y_data_columns as x_tick_labels
        if not x_tick_labels:
            if len(series) == 1:
                box_view.x_tick_labels = y_data_columns

        return box_view.to_dict(params)
