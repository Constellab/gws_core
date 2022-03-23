# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, ParamSet, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.venn_diagram_view import VennDiagramView
from .base_table_view import BaseTableView, Serie1d

if TYPE_CHECKING:
    from ..table import Table

DEFAULT_NUMBER_OF_COLUMNS = 3


class TableVennDiagramView(BaseTableView):
    """
    TableVennDiagramView

    Class for creating Venn diagrams using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "venn-diagram-view",
        "title": str,
        "caption": str,
        "data": {
            "label": str,
            "total_number_of_groups": int
            "group_names": List[str],
            "sections": [
                {
                    "data": [],
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "venn-diagram-view"
    _table: Table

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ListParam(default_value=[]),
    }

    def to_dict(self, params: ConfigParams) -> dict:

        series: List[Serie1d] = params.get_value("series")

        if len(series) < 2 or len(series) > 4:
            raise BadRequestException("The venn diagram only supports from 2 to 4 series (including)")

        view = VennDiagramView()
        for serie in series:
            view.add_group(
                name=serie["name"],
                data=self.get_values_from_selection_range(serie["y"])
            )

        return view.to_dict(params)
