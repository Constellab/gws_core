

from typing import List

from pandas import DataFrame

from .lineplot_2d_view import LinePlot2DView


class StackedBarPlotView(LinePlot2DView):
    """
    StackedBarPlotView

    Show a set of columns as stacked bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "stacked-bar-plot-view",
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

    _type: str = "stacked-bar-plot-view"
    _data: DataFrame
