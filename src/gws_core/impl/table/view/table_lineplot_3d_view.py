# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....resource.view_types import ViewSpecs, ViewType
from ...view.lineplot_3d_view import LinePlot3DView
from .table_scatterplot_3d_view import TableScatterPlot3DView


class TableLinePlot3DView(TableScatterPlot3DView):
    """
    Line3DPlotView

    Class for creating 3d-line plots using a Table.

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
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                        "z": List[Float],
                        "tags": List[Dict[str,str]] | None,
                    },
                    "x_data": str,
                    "y_data": str,
                    "z_column_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _specs: ViewSpecs = {**TableScatterPlot3DView._specs}
    _view_helper = LinePlot3DView
    _type: ViewType = ViewType.LINE_PLOT_3D
