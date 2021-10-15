

from typing import Any, List, Union

import numpy
from pandas import DataFrame

from ....resource.view import ViewSpecs
from ....config.param_spec import IntParam, StrParam, ListParam, BoolParam
from .base_table_view import BaseTableView


class HistogramView(BaseTableView):
    """
    HistogramView

    Show a set of columns as histograms.

    The view model is:
    ------------------

    ```
    {
        "type": "histogram",
        "series": [
            {
                "data": {
                    "hist": List[Float],
                    "bin_edges": List[Float]
                },
                "column_name": str,
            },
            ...
        ]
    }
    ```
    """

    _type: str = "histogram"
    _data: DataFrame
    _specs: ViewSpecs = {
        "column_names": ListParam(human_name="Column names", short_description="List of columns to view"),
        "nbins": IntParam(default_value=10, min_value=0, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
        "density": BoolParam(default_value=False, human_name="Density", short_description="True to plot density"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def to_dict(self, column_names: List[str], nbins: int = 10, density: bool = False, **kwargs) -> dict:
        if nbins <= 0:
            nbins = "auto"

        series = []
        for column_name in column_names:
            col_data = self._data[column_name].values

            hist, bin_edges = numpy.histogram(col_data, bins=nbins, density=density)
            series.append({
                "data": {
                    "hist": hist.tolist(),
                    "bin_edges": bin_edges.tolist(),
                },
                "column_name": column_name,
            })
        return {
            **super().to_dict(**kwargs),
            "series": series
        }
