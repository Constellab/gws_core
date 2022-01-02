# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from .table_view import TableView


class HeatmapView(TableView):
    """
    TableHistogramView

    Class for creating heatmaps using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "heatmap-view",
        "title": str,
        "caption": str,
        "data": dict
    }
    ```

    See also TableView
    """

    _type: str = "heatmap-view"
