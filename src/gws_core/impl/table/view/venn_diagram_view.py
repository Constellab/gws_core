# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....resource.view_types import ViewSpecs
from ...view.venn_diagram_view import VennDiagramView
from .base_table_view import BaseTableView


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
    _data: DataFrame

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns use as groups (max = 3 groups)"),
        "label": StrParam(human_name="Label", optional=True, visibility='protected', short_description="The label to display"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._data
        column_names = params.get_value("column_names")
        if not column_names:
            column_names = data.columns[0:3]

        view = VennDiagramView()
        for i, name in enumerate(column_names):
            view.add_group(
                name=name,
                data=set(data.iloc[:, i].dropna())
            )

        return view.to_dict(params)
