# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view.view_types import ViewSpecs, ViewType
from ...view.barplot_view import BarPlotView
from .base_table_view import BaseTableView
from .table_selection import CellRange, Serie1d, Serie1dList

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableBarPlotView(BaseTableView):
    """
    TableBarPlotView

    Class for creating bar plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "bar-plot-view",
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
                        "tags": List[Dict[str,str]]
                    },
                    "name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ListParam(default_value=[]),
        **BaseTableView._2d_axis_labels_specs
    }
    _type: ViewType = ViewType.BAR_PLOT

    def _get_view(self, params: ConfigParams) -> BarPlotView:
        return BarPlotView()

    def data_to_dict(self, params: ConfigParams) -> dict:
        serie_list: Serie1dList = Serie1dList.from_list(params.get_value("series"))

        if len(serie_list) == 0:
            raise BadRequestException('There must be at least one serie')

        # create view
        view = self._get_view(params)
        view.x_label = params.get_value("x_axis_label")
        view.y_label = params.get_value("y_axis_label")

        view.x_tick_labels = self.get_x_tick_labels_from_series_list(serie_list)

        for serie in serie_list.series:
            y_data = self.get_values_from_selection_range(serie.y)

            view.add_series(
                y=y_data,
                name=serie.name,
                tags=self.get_row_tags_from_selection_range(serie.y)
            )

        return view.data_to_dict(params)
