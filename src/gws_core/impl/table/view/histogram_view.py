

from typing import List

import numpy
from pandas import DataFrame

from ....resource.view import View
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
        "title": str,
        "subtitle": str,
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

    def to_dict(self, column_names: List[str], nbins: int=10, density: bool=False, title: str = None, subtitle: str = None) -> dict:
    
        series = []
        for column_name in column_names:
            col_data = self._data[column_name].values
            if nbins <= 0:
                nbins = "auto"
            hist, bin_edges = numpy.histogram(col_data, bins=nbins, density=density)
            series.append({
                "data": {
                    "hist": hist.tolist(),
                    "bin_edges": bin_edges.tolist(),
                },
                "column_name": column_name,
            })
        return {
            "type": self._type,
            "title": title,
            "subtitle": subtitle,
            "series": series
        }
