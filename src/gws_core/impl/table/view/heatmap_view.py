

from typing import Any, List

import numpy
from pandas import DataFrame

from ....resource.view import View
from .table_view import TableView


class HeatmapView(TableView):
    """
    HistogramView

    Show a set of columns as heatmap. By default all the columns are shown as heatmap.

    The view model is:
    ------------------

    ```
    {
        "type": "heatmap",
        "data": dict
    }
    ```
    """

    _type: str = "heatmap"
    _data: DataFrame