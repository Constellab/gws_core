

from typing import List

import numpy
from pandas import DataFrame

from ....resource.view import View
from .base_table_view import BaseTableView


class HeatmapView(BaseTableView):
    """
    HistogramView

    Show a set of columns as heatmap. By default all the columns are shown as heatmap.

    The view model is:
    ------------------

    ```
    {
        "type": "heatmap",
        "title": str,
        "subtitle": str,
        "data": {},
        "column_names": List[str],
    }
    ```
    """

    _type: str = "heatmap"
    _data: DataFrame

    def to_dict(self, column_names: List[str] = None, scale: int="linear", title: str = None, subtitle: str = None) -> dict:

        series = []
        if column_names:
            data = self._data[ column_names ]

        if scale == "log10":
            data = numpy.log10( data.values )
        elif scale == "log2":
            data = numpy.log2( data.values )
        else:
            data = data.values

        series.append({
            "data": data.tolist(),
            "column_names": column_names,
        })
        return {
            "type": self._type,
            "title": title,
            "subtitle": subtitle,
            "series": series
        }
