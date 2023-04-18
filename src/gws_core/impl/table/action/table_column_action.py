# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, List

from typing_extensions import TypedDict

from gws_core.impl.table.table import Table
from gws_core.task.action.action import Action, action_decorator


class TableAddColumnParam(TypedDict):
    name: str
    index: int


@action_decorator("TableAddColumn")
class TableAddColumn(Action):
    params: TableAddColumnParam

    def execute(self, resource: Table) -> Table:
        resource.add_column(name=self.params["name"], index=self.params["index"])
        return resource

    def undo(self, resource: Table) -> Table:
        resource.remove_column(self.params["name"])
        return resource


class TableRemoveColumnParam(TypedDict):
    name: str
    index: int
    data: List[Any]


@action_decorator("TableRemoveColumn")
class TableRemoveColumn(Action):
    params: TableRemoveColumnParam

    def execute(self, resource: Table) -> Table:
        # save the column data in the params for undo
        self.params["data"] = resource.get_column_data(self.params["name"])
        self.params["index"] = resource.get_column_position_from_name(self.params["name"])
        resource.remove_column(self.params["name"])
        return resource

    def undo(self, resource: Table) -> Table:
        resource.add_column(name=self.params["name"],
                            index=self.params["index"],
                            data=self.params["data"])
        return resource
