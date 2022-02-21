# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .scatterplot_3d_view import ScatterPlot3DView


class LinePlot3DView(ScatterPlot3DView):
    """
    LinePlot3DView

    Base class for creating 3d-line plots.

    The view model is:
    ------------------
    ```
    {
        "type": "line-plot-3d-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "z_label": str,
            "x_tick_labels": List[str] | None,
            "y_tick_labels": List[str] | None,
            "x_tick_tags": List[Dict[str, str]] | None,
            "y_tick_tags": List[Dict[str, str]] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                        "z": List[Float]
                    },
                    "x_name": str,
                    "y_name": str,
                    "z_column_name": str,
                },
                ...
            ]
        }
    }
    ```

    See also ScatterPlot3DView
    """

    _type: str = "line-plot-3d-view"
    _title: str = "3D-Line Plot"
