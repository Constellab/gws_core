

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam
from gws_core.impl.view.barplot_view import BarPlotView
from gws_core.resource.view.view_types import ViewType

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

    _specs = ConfigSpecs({"normalize": BoolParam(default_value=False, optional=True, human_name="Normalize",
                         short_description="True to normalize values"), }).merge_specs(TableBarPlotView._specs)

    _type: ViewType = ViewType.STACKED_BAR_PLOT

    def _get_view(self, params: ConfigParams) -> BarPlotView:
        return StackedBarPlotView(normalize=params.get('normalize'))
