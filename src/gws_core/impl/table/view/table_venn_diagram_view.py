from __future__ import annotations

from typing import TYPE_CHECKING

from gws_core.config.config_specs import ConfigSpecs

from ....config.config_params import ConfigParams
from ....config.param.param_spec import ListParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view.view_types import ViewType
from ...view.venn_diagram_view import VennDiagramView
from .base_table_view import BaseTableView
from .table_selection import Serie1d

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

    _type: ViewType = ViewType.VENN_DIAGRAM
    _table: Table

    _specs = ConfigSpecs(
        {
            "series": ListParam(default_value=[]),
        }
    )

    def data_to_dict(self, params: ConfigParams) -> dict:
        series: list[Serie1d] = Serie1d.from_list(params.get_value("series"))

        if len(series) < 2 or len(series) > 4:
            raise BadRequestException(
                "The venn diagram only supports from 2 to 4 series (including)"
            )

        view = VennDiagramView()
        for serie in series:
            view.add_group(name=serie.name, data=self.get_values_from_selection_range(serie.y))

        return view.data_to_dict(params)
