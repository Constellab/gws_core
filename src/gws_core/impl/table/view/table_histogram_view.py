# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, IntParam, ParamSet, StrParam
from ....resource.view_types import ViewSpecs
from ...view.histogram_view import HistogramView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableHistogramView(BaseTableView):
    """
    TableHistogramView

    Class for creating histograms using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "histogram-view",
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
        "series": ParamSet(
            {
                "y_data_column": StrParam(human_name="Y-data column", short_description="Data to distribute among bins"),
            },
            optional=True,
            human_name="Series of data",
            short_description=f"Select series of data. By default the first {DEFAULT_NUMBER_OF_COLUMNS} columns are plotted",
            max_number_of_occurrences=10
        ),
        "nbins": IntParam(default_value=10, min_value=0, optional=True, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
        "density": BoolParam(default_value=False, optional=True, human_name="Density", short_description="True to plot density"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        nbins = params.get_value("nbins")
        density = params.get_value("density")

        data = self._table.select_numeric_columns().get_data()

        series = params.get_value("series", [])
        if not series:
            n = min(DEFAULT_NUMBER_OF_COLUMNS, data.shape[1])
            series = [{"y_data_column": v} for v in data.columns[0:n]]

        y_data_columns = []
        for param_series in series:
            name = param_series.get("y_data_column")
            y_data_columns.append(name)

        if nbins <= 0:
            nbins = "auto"

        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")

        # create view
        view = HistogramView()
        view.x_label = x_label
        view.y_label = y_label
        view.nbins = nbins
        view.density = density
        for y_data_column in y_data_columns:
            col_data = data[y_data_column].values.tolist()
            name = y_data_column
            view.add_data(data=col_data, name=name)

        return view.to_dict(params)
