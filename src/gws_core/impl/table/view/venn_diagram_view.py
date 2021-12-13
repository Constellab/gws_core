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

    # def _compute_sections(self, data, params):
    #     label = params.get_value("label", "")
    #     column_names = params["column_names"]
    #     bag = {}
    #     for i in range(0, data.shape[1]):
    #         key = data.columns[i]
    #         if key not in column_names:
    #             continue
    #         bag[key] = {
    #             "group_names": [key],
    #             "data": set(data.iloc[:, i].dropna())
    #         }

    #     found = True
    #     while found:
    #         found = False
    #         bag_copy = copy.deepcopy(bag)
    #         for key1, val1 in bag.items():
    #             for key2, val2 in bag.items():
    #                 if key1 == key2:
    #                     continue
    #                 columns = list(set([*val1["group_names"], *val2["group_names"]]))
    #                 skip = False
    #                 for c in columns:
    #                     if c not in column_names:
    #                         skip = True
    #                         break
    #                 if skip:
    #                     continue
    #                 columns.sort()
    #                 joined_key = "_".join(columns)
    #                 if joined_key not in bag:
    #                     inter1 = set([str(k) for k in val1["data"]])
    #                     inter2 = set([str(k) for k in val2["data"]])
    #                     bag_copy[joined_key] = {
    #                         "group_names": columns,
    #                         "data": inter1.intersection(inter2)
    #                     }
    #                     found = True
    #         bag = bag_copy

    #     _data_dict = {
    #         "label": label,
    #         "total_number_of_groups": len(column_names),
    #         "group_names": column_names,
    #         "sections": list(bag.values()),
    #     }
    #     return _data_dict

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
