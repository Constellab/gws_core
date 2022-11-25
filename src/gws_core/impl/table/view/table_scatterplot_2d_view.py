# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List, Type

from ....config.config_types import ConfigParams
from ....config.param.param_spec import ListParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view.view_types import ViewSpecs, ViewType
from ...view.scatterplot_2d_view import ScatterPlot2DView
from .base_table_view import BaseTableView
from .table_selection import Serie2d

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableScatterPlot2DView(BaseTableView):
    """
    TableScatterPlot2DView

    Class for creating 2d-scatter plots using a Table.

    The view model is:
    ------------------
    ```
    {
        "type": "scatter-plot-2d-view",
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
                    "name": str,
                },
                ...
            ]
        }
    }
    ```

    See also ScatterPlot2DView
    """

    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ListParam(default_value=[]),
        **BaseTableView._2d_axis_labels_specs
    }
    _view_helper: Type = ScatterPlot2DView
    _type: ViewType = ViewType.SCATTER_PLOT_2D

    def data_to_dict(self, params: ConfigParams) -> dict:
        if not issubclass(self._view_helper, ScatterPlot2DView):
            raise BadRequestException("Invalid view helper. An subclass of ScatterPlot2DView is expected")

        series: List[Serie2d] = Serie2d.from_list(params.get_value("series"))

        if len(series) == 0:
            raise BadRequestException('There must be at least one serie')

        # create view
        view = self._view_helper()
        view.x_label = params.get_value("x_axis_label")
        view.y_label = params.get_value("y_axis_label")

        for serie in series:
            y_data = self.get_values_from_selection_range(serie.y)

            x_data: List[float] = None
            if serie.x is not None:
                x_data = self.get_values_from_selection_range(serie.x)

            view.add_series(
                x=x_data,
                y=y_data,
                name=serie.name,
                tags=self.get_row_tags_from_selection_range(serie.y)
            )

        return view.data_to_dict(params)
