

from typing import List

from pandas import DataFrame

from .scatterplot_2d_view import ScatterPlot2DView


class LinePlot2DView(ScatterPlot2DView):
    """
    ScatterPlot2DView

    Show a set of columns as 2d-line plots.

    The view model is:
    ------------------

    ```
    {
        "type": "line-2d-plot-view",
        "title": str,
        "subtitle": str,
        "series": [
            {
                "data": {
                    "x": List[Float],
                    "y": List[Float],
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

    _type: str="line-plot-2d-view"
    _data: DataFrame
