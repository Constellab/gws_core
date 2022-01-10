# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, ParamSet, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.scatterplot_2d_view import ScatterPlot2DView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableScatterPlot2DView(BaseTableView):
    """
    TableScatterPlot2DView

    Class for creating 2d-scatter plots using a Table.

    The view model is:
    ------------------
    ```
    {
        "type": "scatter-plot-2d-view",
        "title": str,
        "caption": str,
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
                    "x_name": str,
                    "y_name": str,
                },
                ...
            ]
        }
    }
    ```

    See also ScatterPlot2DView
    """

    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ParamSet(
            {
                "x_data_column": StrParam(human_name="X-data column", optional=True, default_value=None),
                "y_data_column": StrParam(human_name="Y-data column"),
            },
            optional=True,
            human_name="Series of data",
            short_description=f"Select series of data. By default the first {DEFAULT_NUMBER_OF_COLUMNS} columns used as Y-data",
            max_number_of_occurrences=10
        ),
        "x_label": StrParam(human_name="X-axis label", optional=True, default_value=None, visibility=StrParam.PROTECTED_VISIBILITY),
        "y_label": StrParam(human_name="Y-axis label", optional=True, default_value=None, visibility=StrParam.PROTECTED_VISIBILITY),
        "x_tick_labels": ListParam(human_name="X-tick labels", optional=True, visibility=ListParam.PROTECTED_VISIBILITY, short_description="The labels of x-axis ticks"),
    }
    _view_helper: Type = ScatterPlot2DView

    def to_dict(self, params: ConfigParams) -> dict:
        if not issubclass(self._view_helper, ScatterPlot2DView):
            raise BadRequestException("Invalid view helper. An subclass of ScatterPlot2DView is expected")

        data = self._table.get_data()

        # continue ...
        x_data_columns = []
        y_data_columns = []
        series = params.get_value("series", [])
        if not series:
            n = min(DEFAULT_NUMBER_OF_COLUMNS, data.shape[1])
            series = [{"y_data_column": v} for v in data.columns[0:n]]

        for param_series in series:
            x_data_columns.append(param_series.get("x_data_column"))
            y_data_columns.append(param_series.get("y_data_column"))

        print(x_data_columns)

        self.check_column_names(x_data_columns)
        self.check_column_names(y_data_columns)

        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")

        x_tick_labels = params.get_value("x_tick_labels", [])

        # create view
        view = self._view_helper()
        view.x_label = x_label
        view.y_label = y_label
        view.x_tick_labels = x_tick_labels

        for i, y_data_column in enumerate(y_data_columns):
            y_data = data[y_data_column].fillna('').values.tolist()
            x_data_column = x_data_columns[i]
            if x_data_column:
                x_data = data[x_data_column].fillna('').values.tolist()
            else:
                x_data = list(range(0, data.shape[0]))
            view.add_series(x=x_data, y=y_data, x_name=x_data_column, y_name=y_data_column)

        return view.to_dict(params)
