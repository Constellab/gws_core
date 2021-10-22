

from typing import List

from pandas import DataFrame

from .lineplot_2d_view import LinePlot2DView


class BarPlotView(LinePlot2DView):
    """
    BarPlotView

    Show a set of columns as bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "bar-plot-view",
        "data": [
            {
                "data": {
                    "x": List[Float],
                    "y": List[Float]
                },
                "x_column_name": str,
                "y_column_name": str,
            },
            ...
        ],
        "x_label": str,
        "y_label": str,
    }
    ```
    """

    _type: str = "bar-plot-view"
    _data: DataFrame
