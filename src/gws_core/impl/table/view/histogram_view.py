

from typing import Any, List, Union

import numpy
from pandas import DataFrame

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

    column_names: List[str]
    nbins: int
    density: bool

    def __init__(self, data: Any, column_names: List[str], nbins: int = 10, density: bool = False):
        super().__init__(data)
        self.column_names = column_names
        self.nbins = nbins
        self.density = density

    def get_nbins(self) -> Union[int, str]:
        if self.nbins <= 0:
            return "auto"
        return self.nbins

    def to_dict(self) -> dict:

        series = []
        for column_name in self.column_names:
            col_data = self._data[column_name].values

            hist, bin_edges = numpy.histogram(col_data, bins=self.get_nbins(), density=self.density)
            series.append({
                "data": {
                    "hist": hist.tolist(),
                    "bin_edges": bin_edges.tolist(),
                },
                "column_name": column_name,
            })
        return {
            "type": self._type,
            "series": series
        }
