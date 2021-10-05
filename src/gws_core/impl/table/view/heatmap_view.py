

from typing import Any, List

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
        "data": {},
        "column_names": List[str],
    }
    ```
    """

    _type: str = "heatmap"
    _data: DataFrame

    column_names: List[str]
    scale: int

    def __init__(self, data: Any, column_names: List[str] = None, scale: int = "linear"):
        super().__init__(data)
        self.column_names = column_names
        self.scale = scale

    def to_dict(self) -> dict:

        series = []
        if self.column_names:
            data = self._data[self.column_names]

        if self.scale == "log10":
            data = numpy.log10(data.values)
        elif self.scale == "log2":
            data = numpy.log2(data.values)
        else:
            data = data.values

        series.append({
            "data": data.tolist(),
            "column_names": self.column_names,
        })
        return {
            "type": self._type,
            "series": series
        }
