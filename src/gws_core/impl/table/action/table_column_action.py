# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import TypedDict

from gws_core.impl.table.table import Table
from gws_core.task.action.actions import Action, action_decorator


class AddColumnParam(TypedDict):
    name: str
    index: int


@action_decorator("TableAddColumn")
class TableAddColumn(Action):
    params: AddColumnParam

    def execute(self, resource: Table) -> Table:
        resource.add_column(column_name=self.params["name"], column_index=self.params["index"])
        return resource

    def undo(self, resource: Table) -> Table:
        return super().undo(resource)
