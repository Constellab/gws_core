# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import math
from typing import Dict, List, Union

from ...config.config_types import ConfigParams
from ...resource.view import View


class VennDiagramView(View):
    """
    VennDiagramView

    Base class for creating Venn diagrams.

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
                    "group_names": List[str],
                    "data": [],
                },
                ...
            ]
        }
    }
    ```
    """

    label: str = None
    _groups: Dict[str, set] = None
    _type: str = "bar-plot-view"

    def _compute_sections(self):
        group_names = list(self._groups.keys())
        bag = {}
        for key, data in self._groups.items():
            bag[key] = {
                "group_names": [key],
                "data": data  # dropna
            }

        found = True
        while found:
            found = False
            bag_copy = copy.deepcopy(bag)
            for key1, val1 in bag.items():
                for key2, val2 in bag.items():
                    if key1 == key2:
                        continue
                    columns = list(set([*val1["group_names"], *val2["group_names"]]))
                    skip = False
                    for c in columns:
                        if c not in group_names:
                            skip = True
                            break
                    if skip:
                        continue
                    columns.sort()
                    joined_key = "_".join(columns)
                    if joined_key not in bag:
                        inter1 = set([str(k) for k in val1["data"]])
                        inter2 = set([str(k) for k in val2["data"]])
                        bag_copy[joined_key] = {
                            "group_names": columns,
                            "data": inter1.intersection(inter2)
                        }
                        found = True
            bag = bag_copy

        _data_dict = {
            "label": self.label,
            "total_number_of_groups": len(group_names),
            "group_names": group_names,
            "sections": list(bag.values()),
        }
        return _data_dict

    def add_group(self, name: str, data: Union[set, list]):
        if not self._groups:
            self._groups = {}
        data = [str(x) for x in data]
        self._groups[name] = set(data)

    def to_dict(self, params: ConfigParams) -> dict:
        _data_dict = self._compute_sections()
        return {
            **super().to_dict(params),
            "data": _data_dict
        }