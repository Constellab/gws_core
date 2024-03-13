

from __future__ import annotations

from typing import TYPE_CHECKING, List

from gws_core.config.config_params import ConfigParams
from gws_core.config.param.param_spec import FloatParam, ListParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.view.base_table_view import BaseTableView
from gws_core.impl.table.view.table_selection import Serie2d
from gws_core.impl.view.vulcano_plot_view import VulcanoPlotView
from gws_core.resource.view.view_types import ViewSpecs, ViewType

if TYPE_CHECKING:
    from ..table import Table


class TableVulcanoPlotView(BaseTableView):

    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ListParam(default_value=[]),
        "x_threshold": FloatParam(default_value=0.05),
        "y_threshold": FloatParam(default_value=0.05),
        **BaseTableView._2d_axis_labels_specs,

    }
    _type: ViewType = ViewType.VULCANO_PLOT

    def data_to_dict(self, params: ConfigParams) -> dict:

        series: List[Serie2d] = Serie2d.from_list(params.get_value("series"))

        if len(series) != 1:
            raise BadRequestException('There must be only one series')
        serie = series[0]

        # create view
        view = VulcanoPlotView(params.get_value("x_threshold"), params.get_value("y_threshold"))
        # for the labels, use the name provided by the user or the name of the selections
        view.x_label = params.get_value("x_axis_label") or serie.get_x_selection_name()
        view.y_label = params.get_value("y_axis_label") or serie.get_y_selection_name()

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
