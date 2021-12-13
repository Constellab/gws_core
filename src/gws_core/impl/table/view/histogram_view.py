# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import numpy
from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ....resource.view_types import ViewSpecs
from ...view.histogram_view import HistogramView
from .base_table_view import BaseTableView

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

    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to view"),
        "nbins": IntParam(default_value=10, min_value=0, optional=True, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
        "density": BoolParam(default_value=False, optional=True, human_name="Density", short_description="True to plot density"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        nbins = params.get_value("nbins")
        column_names = params.get_value("column_names", [])
        density = params.get_value("density")

        if nbins <= 0:
            nbins = "auto"
        if not column_names:
            n = min(self._data.shape[1], MAX_NUMBERS_OF_COLUMNS_PER_PAGE)
            column_names = self._data.columns[0:n]

        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")

        # create view
        view = HistogramView()
        view.x_label = x_label
        view.y_label = y_label
        for column_name in column_names:
            col_data = self._data[column_name].values
            hist, bin_edges = numpy.histogram(col_data, bins=nbins, density=density)
            bin_centers = (bin_edges[0:-2] + bin_edges[1:-1])/2
            view.add_series(
                x=bin_centers.tolist(),
                y=hist.tolist(),
                name=column_name
            )

        return view.to_dict(params)
