# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from ....config.config_types import ConfigParams
from ....config.param_spec import ParamSet, StrParam
from ....resource.view_types import ViewSpecs
from ...view.venn_diagram_view import VennDiagramView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table


class TableVennDiagramView(BaseTableView):
    """
    TableVennDiagramView

    Class for creating Venn diagrams using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "venn-diagram-view",
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
                "data_column": StrParam(human_name="Data column", short_description="Data that represents a group"),
            },
            human_name="Series of data",
            max_number_of_occurrences=4
        ),
        "label": StrParam(human_name="Label", optional=True, visibility=StrParam.PROTECTED_VISIBILITY, short_description="The label of the plot"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._table.get_data()

        #column_names = params.get_value("column_names")
        data_columns = []
        for param_series in params.get_value("series", []):
            name = param_series["data_column"]
            data_columns.append(name)

        if not data_columns:
            data_columns = data.columns[0:3]

        view = VennDiagramView()
        for i, name in enumerate(data_columns):
            view.add_group(
                name=name,
                data=set(data.iloc[:, i].dropna())
            )

        return view.to_dict(params)
