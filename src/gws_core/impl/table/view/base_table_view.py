# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from pandas import DataFrame

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....resource.view import View

if TYPE_CHECKING:
    from ..table import Table


class BaseTableView(View):
    _type: str
    _table: Table

    def __init__(self, table: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._check_and_set_data(table)

    def _check_and_set_data(self, table: Table):
        from ..table import Table
        if not isinstance(table, Table):
            raise BadRequestException("The data must be a Table resource")
        self._table = table

    def get_table(self):
        return self._table

    def check_column_names(self, column_names):
        for name in column_names:
            if name not in self._table.get_data().columns:
                raise BadRequestException(f"The column name '{name}' is not valid")
