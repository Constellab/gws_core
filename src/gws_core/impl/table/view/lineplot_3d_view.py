

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
        "type": "line-plot-3d",
        "title": str,
        "subtitle": str,
        "series": [
            {
                "data": {
                    "x": List[Float],
                    "y": List[Float],
                    "z": List[Float]
                },
                "x_label": str,
                "y_label": str,
                "z_label": str
            },
            ...
        ]
    }
    ```
    """

    _type: str = "line-plot-3d"
    _data: DataFrame
