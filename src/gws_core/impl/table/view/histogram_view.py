# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, IntParam, ParamSet, StrParam
from ....resource.view_types import ViewSpecs
from ...view.histogram_view import HistogramView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table

MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 999


class TableHistogramView(BaseTableView):
    """
    TableHistogramView

    Class for creating histograms using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "histogram-view",
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
            human_name="Series of Y-data",
            max_number_of_occurrences=10
        ),
        "nbins": IntParam(default_value=10, min_value=0, optional=True, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
        "density": BoolParam(default_value=False, optional=True, human_name="Density", short_description="True to plot density"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        nbins = params.get_value("nbins")
        #column_names = params.get_value("column_names", [])
        density = params.get_value("density")

        data = self._table.get_data()

        y_data_columns = []
        for param_series in params.get_value("series", []):
            name = param_series["y_data_column"]
            y_data_columns.append(name)

        if nbins <= 0:
            nbins = "auto"
        if not y_data_columns:
            n = min(data.shape[1], MAX_NUMBERS_OF_COLUMNS_PER_PAGE)
            y_data_columns = data.columns[0:n]

        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")

        # create view
        view = HistogramView()
        view.x_label = x_label
        view.y_label = y_label
        for y_data_column in y_data_columns:
            col_data = data[y_data_column].values
            hist, bin_edges = numpy.histogram(col_data, bins=nbins, density=density)
            bin_centers = (bin_edges[0:-2] + bin_edges[1:-1])/2
            view.add_series(
                x=bin_centers.tolist(),
                y=hist.tolist(),
                name=y_data_column
            )

        return view.to_dict(params)
