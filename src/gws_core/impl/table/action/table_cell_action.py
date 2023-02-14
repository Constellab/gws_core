# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any

from typing_extensions import TypedDict

from gws_core.impl.table.table import Table
from gws_core.task.action.action import Action


class TableUpdateCellParam(TypedDict):
    row: int
    column: int
    new_value: Any
    old_value: Any


class TableUpdateCell(Action):
    params: TableUpdateCellParam

    def execute(self, resource: Table) -> Table:
        self.params["old_value"] = resource.get_cell_value_at(self.params["row"],
                                                              self.params["column"])

        resource.set_cell_value_at(self.params["row"],
                                   self.params["column"],
                                   self.params["new_value"])
        return resource

    def undo(self, resource: Table) -> Table:
        resource.set_cell_value_at(self.params["row"],
                                   self.params["column"],
                                   self.params["old_value"])
        return resource
