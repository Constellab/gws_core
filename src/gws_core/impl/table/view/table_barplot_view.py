# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from pandas.api.types import is_numeric_dtype

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, ParamSet, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.barplot_view import BarPlotView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableBarPlotView(BaseTableView):
    """
    TableBarPlotView

    Class for creating bar plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "bar-plot-view",
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
                        "tags": List[Dict[str,str]]
                    },
                    "name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series":
        ParamSet(
            {"y_data_column": StrParam(human_name="Y-data column"), },
            optional=True, human_name="Series of data",
            short_description=f"Select series of data. By default the first {DEFAULT_NUMBER_OF_COLUMNS} columns are plotted",
            max_number_of_occurrences=10),
        "x_label":
        StrParam(
            human_name="X-axis label", optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            short_description="The x-axis label to display"),
        "y_label":
        StrParam(
            human_name="Y-axis label", optional=True, visibility=StrParam.PROTECTED_VISIBILITY,
            short_description="The y-axis label to display"),
        "x_tick_labels":
        ListParam(
            human_name="X-tick labels", optional=True, visibility=ListParam.PROTECTED_VISIBILITY,
            short_description="The labels of x-axis ticks. By default, the data index is used")}
    _view_helper = BarPlotView

    def to_dict(self, params: ConfigParams) -> dict:
        if not issubclass(self._view_helper, BarPlotView):
            raise BadRequestException("Invalid view helper. An subclass of BarPlotView is expected")

        data = self._table.select_numeric_columns().get_data()

        series = params.get_value("series", [])
        if not series:
            n = min(DEFAULT_NUMBER_OF_COLUMNS, data.shape[1])
            series = [{"y_data_column": v} for v in data.columns[0:n]]

        # select columns
        y_data_columns = []
        for param_series in series:
            name = param_series["y_data_column"]
            y_data_columns.append(name)

        self.check_column_names(y_data_columns)

        # continue ...
        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")
        x_tick_labels = params.get_value("x_tick_labels", data.index.values.tolist())

        # create view
        view = self._view_helper()
        view.x_label = x_label
        view.y_label = y_label
        view.x_tick_labels = x_tick_labels
        for column_name in y_data_columns:
            #y_data = data[column_name]
            # if not is_numeric_dtype(y_data):
            #    continue
            y_data = data[column_name].fillna('').values.tolist()

            extended_row_tags = self._table.get_row_tags()
            extended_row_tags = [{"name": column_name, **t} for t in extended_row_tags]
            view.add_series(
                x=list(range(0, len(y_data))),
                y=y_data,
                name=column_name,
                tags=extended_row_tags
            )

        return view.to_dict(params)
