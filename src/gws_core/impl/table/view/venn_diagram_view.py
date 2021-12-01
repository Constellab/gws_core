# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....resource.view_types import ViewSpecs
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from .base_table_view import BaseTableView


class VennDiagramView(BaseTableView):
    """
    BarPlotView

    Show a set of columns as bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "venn-diagramm-view",
        "data": {
            "label": str,
            "total_number_of_columns": int
            "sections": [
                {
                    "column_names": List[str],
                    "section": [],
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "venn_diagram-plot-view"
    _data: DataFrame

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns use as groups (max = 3 groups)"),
        "numeric_data_filters": NumericDataFilterParamConstructor.construct_filter(visibility='protected'),
        "text_data_filters": TextDataFilterParamConstructor.construct_filter(visibility='protected'),
        "label": StrParam(human_name="Label", optional=True, visibility='protected', short_description="The label to display"),
    }

    def _compute_sections(self, data, params):
        label = params.get_value("label", "")
        column_names = params["column_names"]
        bag = {}
        for i in range(0, data.shape[1]):
            key = data.columns[i]
            if key not in column_names:
                continue
            bag[key] = {
                "columns": [key],
                "section": set(data.iloc[:, i].dropna())
            }

        found = True
        while found:
            found = False
            bag_copy = copy.deepcopy(bag)
            for key1, val1 in bag.items():
                for key2, val2 in bag.items():
                    if key1 == key2:
                        continue
                    columns = list(set([*val1["columns"], *val2["columns"]]))
                    skip = False
                    for c in columns:
                        if c not in column_names:
                            skip = True
                            break
                    if skip:
                        continue
                    columns.sort()
                    joined_key = "_".join(columns)
                    if joined_key not in bag:
                        inter1 = set([str(k) for k in val1["section"]])
                        inter2 = set([str(k) for k in val2["section"]])
                        bag_copy[joined_key] = {
                            "columns": columns,
                            "section": inter1.intersection(inter2)
                        }
                        found = True
            bag = bag_copy

        _data_dict = {
            "label": label,
            "total_number_of_columns": len(column_names),
            "sections": list(bag.values()),
        }
        return _data_dict

    def to_dict(self, params: ConfigParams) -> dict:
        # apply pre-filters
        data = self._data
        data = NumericDataFilterParamConstructor.validate_filter("numeric_data_filters", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_data_filters", data, params)
        column_names = params.get_value("column_names")
        if not column_names:
            params["column_names"] = data.columns[0:3]

        # continue ...
        _data_dict = self._compute_sections(data, params)

        return {
            **super().to_dict(params),
            "data": _data_dict
        }
