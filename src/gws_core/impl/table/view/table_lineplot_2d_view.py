

from ....resource.view.view_types import ViewType
from ...view.lineplot_2d_view import LinePlot2DView
from .table_scatterplot_2d_view import TableScatterPlot2DView


class TableLinePlot2DView(TableScatterPlot2DView):
    """
    TableScatterPlot2DView

    Class for creating 2d-line plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "line-2d-plot-view",
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
                        "tags": List[Dict[str,str]] | None,
                    },
                    "x_data": str,
                    "y_data": str,
                },
                ...
            ]
        }
    }
    ```

    See also ScatterPlot2DView, LinePlot2DView, TableScatterPlot2DView
    """

    _view_helper = LinePlot2DView

    _type: ViewType = ViewType.LINE_PLOT_2D
