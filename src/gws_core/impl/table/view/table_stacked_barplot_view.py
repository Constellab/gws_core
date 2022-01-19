# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...view.stacked_barplot_view import StackedBarPlotView
from .table_barplot_view import TableBarPlotView


class TableStackedBarPlotView(TableBarPlotView):
    """
    TableStackedBarPlotView

    Class for creating stacked-bar plots using a Table.

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
    """

    _view_helper = StackedBarPlotView
