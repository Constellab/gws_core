# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ....config.config_params import ConfigParams
from ....config.param.param_spec import ListParam
from ....resource.view.view_types import ViewSpecs, ViewType
from ...view.boxplot_view import BoxPlotView
from .base_table_view import BaseTableView
from .table_selection import Serie1d

if TYPE_CHECKING:
    from ..table import Table


class TableBoxPlotView(BaseTableView):
    """
    TableBarPlotView

    Class for creating box plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str],
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "max": List[Float],
                        "q1": List[Float],
                        "median": List[Float],
                        "min": List[Float],
                        "q3": List[Float],
                        "lower_whisker": List[Float],
                        "upper_whisker": List[Float],
                    }
                },
                ...
            ]
        }
    }
    ```

    See also BoxPlotView
    """

    DEFAULT_NUMBER_OF_COLUMNS = 3

    _type: ViewType = ViewType.BOX_PLOT
    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ListParam(default_value=[]),
        **BaseTableView._2d_axis_labels_specs
    }

    def data_to_dict(self, params: ConfigParams) -> dict:

        series: List[Serie1d] = Serie1d.from_list(params.get_value("series"))

        if len(series) == 0:
            raise BadRequestException('There must be at least one serie')

        box_view = BoxPlotView()
        box_view.x_label = params.get_value("x_axis_label")
        box_view.y_label = params.get_value("y_axis_label")

        for serie in series:
            data = self.get_values_from_selection_range(serie.y)
            tags = self.get_single_column_tags_from_selection_range(serie.y)
            box_view.add_data(
                data=data,
                name=serie.name,
                tags=tags
            )

        return box_view.data_to_dict(params)
