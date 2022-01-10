# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from ....config.config_types import ConfigParams
from ....config.param_spec import ParamSet, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.venn_diagram_view import VennDiagramView
from .base_table_view import BaseTableView

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
        "series": ParamSet(
            {
                "data_column": StrParam(human_name="Data column", optional=True, short_description="Data that represents a group"),
            },
            optional=True,
            human_name="Series of data",
            max_number_of_occurrences=4
        ),
        "label": StrParam(human_name="Label", optional=True, visibility=StrParam.PROTECTED_VISIBILITY, short_description="The label of the plot"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._table.get_data()

        series = params.get_value("series", [])
        if not series:
            n = min(DEFAULT_NUMBER_OF_COLUMNS, data.shape[1])
            series = [{"data_column": v} for v in data.columns[0:n]]

        if len(series) <= 1:
            raise BadRequestException("At list 2 columns are required to plot a Venn diagram")

        data_columns = []
        for param_series in series:
            name = param_series["data_column"]
            data_columns.append(name)

        view = VennDiagramView()
        for i, name in enumerate(data_columns):
            view.add_group(
                name=name,
                data=set(data.iloc[:, i].dropna())
            )

        return view.to_dict(params)
