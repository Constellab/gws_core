# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .scatterplot_2d_view import ScatterPlot2DView


class LinePlot2DView(ScatterPlot2DView):
    """
    LinePlot2DView

    Base class for creating 2d-line plots.

    The view model is:
    ------------------
    ```
    {
        "type": "line-plot-2d-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                    },
                    "x_name": str,
                    "y_name": str,
                },
                ...
            ]
        }
    }
    ```

    See also ScatterPlot2DView
    """

    _type: str = "line-plot-2d-view"