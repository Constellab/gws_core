

from pandas import DataFrame

from .scatterplot_3d_view import ScatterPlot3DView


class LinePlot3DView(ScatterPlot3DView):
    """
    Line3DPlotView

    Show a set of columns as 3d-line plots.

    The view model is:
    ------------------

    ```
    {
        "type": "line-plot-3d-view",
        "data": [
            {
                "data": {
                    "x": List[Float],
                    "y": List[Float],
                    "z": List[Float]
                },
                "x_column_name": str,
                "y_column_name": str,
                "z_column_name": str,
            },
            ...
        ],
        "x_label": str,
        "y_label": str,
        "z_label": str,
    }
    ```
    """

    _type: str = "line-plot-3d-view"
    _data: DataFrame
