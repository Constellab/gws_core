# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.utils import Utils

from ....config.config_params import ConfigParams
from ....config.param.param_spec import IntParam, ListParam, StrParam
from ....resource.view.view_types import ViewSpecs, ViewType
from ...view.histogram_view import HistogramMode, HistogramView
from .base_table_view import BaseTableView
from .table_selection import Serie1d

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableHistogramView(BaseTableView):
    """
    TableHistogramView

    Class for creating histograms using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "histogram-view",
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
        "nbins": IntParam(default_value=10, min_value=0, optional=True, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
        "mode": StrParam(default_value="FREQUENCY", optional=True, human_name="Mode",
                         allowed_values=Utils.get_literal_values(HistogramMode)),
        **BaseTableView._2d_axis_labels_specs
    }
    _type: ViewType = ViewType.HISTOGRAM

    def data_to_dict(self, params: ConfigParams) -> dict:
        series: List[Serie1d] = Serie1d.from_list(params.get_value("series"))

        if len(series) == 0:
            raise BadRequestException('There must be at least one serie')

        # create view
        view = HistogramView(nbins=params.get_value("nbins"), mode=params.get_value("mode"))
        view.x_label = params.get_value("x_axis_label")
        view.y_label = params.get_value("y_axis_label")

        for serie in series:
            view.add_data(
                data=self.get_values_from_selection_range(serie.y),
                name=serie.name)

        return view.data_to_dict(params)
