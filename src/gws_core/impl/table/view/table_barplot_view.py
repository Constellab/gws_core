# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List

from pandas.api.types import is_numeric_dtype

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, ParamSet, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.barplot_view import BarPlotView
from .base_table_view import BaseTableView, Serie1d, Serie2d

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
        "series": ListParam(default_value=[])
    }
    _view_helper = BarPlotView

    def to_dict(self, params: ConfigParams) -> dict:
        if not issubclass(self._view_helper, BarPlotView):
            raise BadRequestException("Invalid view helper. An subclass of BarPlotView is expected")

        series: List[Serie1d] = params.get_value("series")

        if len(series) == 0:
            raise BadRequestException('There must be at least one serie')

        # create view
        view = self._view_helper()

        for serie in series:
            y_data = self.get_selection_range_values(serie["y"])

            view.add_series(
                y=y_data,
                name=serie["name"],
                tags=self.get_row_tags_from_selection_range(serie["y"])
            )

        return view.to_dict(params)
