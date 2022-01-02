# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .barplot_view import BarPlotView


class StackedBoxPlotView(BarPlotView):
    """
    StackedBoxPlotView

    Base class for creating stacked-bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "stacked-bar-plot-view",
        "title": str,
        "caption": str,
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
                    "name": str,
                },
                ...
            ]
        }
    }
    ```

    See also BarPlotView
    """

    _type: str = "stacked-bar-plot-view"
    _title: str = "Stacked-Bar Plot"
