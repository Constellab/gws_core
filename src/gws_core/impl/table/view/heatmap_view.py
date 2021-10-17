

from typing import Any, List

import numpy
from pandas import DataFrame

from ....config.param_spec import StrParam
from ....resource.view_types import ViewSpecs
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
        "type": "heatmap-view",
        "title": str,
        "subtitle": str,
        "data": dict
    }
    ```
    """

    _type: str = "heatmap-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **TableView._specs,
        "scale": StrParam(default_value="none", optional=True, allowed_values=["none", "log10", "log2"], visibility='protected', human_name="Scaling factor to apply"),
    }