# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, IntParam, ListParam
from ....resource.view_types import ViewSpecs, ViewType
from ...view.histogram_view import HistogramView
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
        "density": BoolParam(default_value=False, optional=True, human_name="Density", short_description="True to plot density"),
    }
    _type: ViewType = ViewType.HISTOGRAM

    def data_to_dict(self, params: ConfigParams) -> dict:
        nbins = params.get_value("nbins")
        density = params.get_value("density")

        series: List[Serie1d] = Serie1d.from_list(params.get_value("series"))

        if len(series) == 0:
            raise BadRequestException('There must be at least one serie')

        if nbins is None or nbins <= 0:
            nbins = "auto"

        # create view
        view = HistogramView()
        view.nbins = nbins
        view.density = density
        for serie in series:
            view.add_data(
                data=self.get_values_from_selection_range(serie.y),
                name=serie.name)

        return view.data_to_dict(params)
