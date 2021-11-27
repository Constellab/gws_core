# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from .barplot_view import BarPlotView


class StackedBarPlotView(BarPlotView):
    """
    StackedBarPlotView

    Show a set of columns as stacked bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "stacked-bar-plot-view",
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
                    "x_column_name": str,
                    "column_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "stacked-bar-plot-view"
    _data: DataFrame
