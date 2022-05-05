# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.config_types import ConfigParams
from gws_core.config.param_spec import BoolParam
from gws_core.impl.table.view.base_table_view import BaseTableView
from gws_core.impl.view.barplot_view import BarPlotView
from gws_core.resource.view_types import ViewSpecs, ViewType

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
                        "tags": List[Dict[str,str]] | None,
                    },
                    "name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _specs: ViewSpecs = {
        **TableBarPlotView._specs,
        "normalize": BoolParam(default_value=False, optional=True, human_name="Normalize", short_description="True to normalize values"),
    }
    _type: ViewType = ViewType.STACKED_BAR_PLOT

    def _get_view(sekf, params: ConfigParams) -> BarPlotView:
        return StackedBarPlotView(normalize=params.get('normalize'))
