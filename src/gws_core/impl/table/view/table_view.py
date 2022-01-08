# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import IntParam, StrParam
from ....resource.view_types import ViewSpecs
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table

MAX_NUMBERS_OF_ROWS_PER_PAGE = 100
MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 999


class TableView(BaseTableView):
    """
    Class table view.

    This class creates tabular view using a Table.

    The view model is:
    ```
    {
        "type": "table"
        "title": str,
        "caption": str,
        "data": dict,
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
    }
    ```
    """

    _type = "table-view"
    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs, "from_row": IntParam(default_value=1, human_name="From row"),
        "number_of_rows_per_page":
        IntParam(
            default_value=MAX_NUMBERS_OF_ROWS_PER_PAGE, max_value=MAX_NUMBERS_OF_ROWS_PER_PAGE, min_value=1,
            human_name="Number of rows per page"),
        "from_column": IntParam(default_value=1, human_name="From column"),
        "number_of_columns_per_page":
        IntParam(
            default_value=MAX_NUMBERS_OF_COLUMNS_PER_PAGE, max_value=MAX_NUMBERS_OF_COLUMNS_PER_PAGE, min_value=1,
            human_name="Number of columns per page"),
        'replace_nan_by':
        StrParam(
            default_value="empty", allowed_values=["empty", "NaN", "-"],
            optional=True, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Replace NaN by",
            short_description="Text to use to replace NaN values. Defaults to empty string"), }

    MAX_NUMBERS_OF_ROWS_PER_PAGE = MAX_NUMBERS_OF_ROWS_PER_PAGE
    MAX_NUMBERS_OF_COLUMNS_PER_PAGE = MAX_NUMBERS_OF_COLUMNS_PER_PAGE

    def _slice(self, data: DataFrame, from_row_index: int, to_row_index: int,
               from_column_index: int, to_column_index: int, replace_nan_by: str = "") -> dict:
        last_row_index = data.shape[0]
        last_column_index = data.shape[1]
        from_row_index = min(max(from_row_index, 0), last_row_index-1)
        from_column_index = min(max(from_column_index, 0), last_column_index-1)
        to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBERS_OF_ROWS_PER_PAGE), last_row_index)
        to_column_index = min(
            min(to_column_index, from_column_index + self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE),
            last_column_index)

        # Remove NaN values to convert to json
        data: DataFrame = data.fillna(replace_nan_by)

        return data.iloc[
            from_row_index:to_row_index,
            from_column_index:to_column_index,
        ].to_dict('list')

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._table.get_data()

        # continue ...
        from_row: int = params.get("from_row")
        number_of_rows_per_page: int = params.get("number_of_rows_per_page")
        from_column: int = params.get("from_column")
        number_of_columns_per_page: int = params.get("number_of_columns_per_page")
        replace_nan_by: str = params.get("replace_nan_by", "")
        if replace_nan_by == "empty":
            replace_nan_by = ""

        total_number_of_rows = data.shape[0]
        total_number_of_columns = data.shape[1]

        from_row_index: int = from_row - 1
        from_column_index: int = from_column - 1
        to_row_index: int = from_row_index + number_of_rows_per_page
        to_column_index: int = from_column_index + number_of_columns_per_page

        data = self._slice(
            data,
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index,
            replace_nan_by=replace_nan_by)

        return {
            **super().to_dict(params),
            "data": data,
            "from_row": from_row_index,
            "number_of_rows_per_page": number_of_rows_per_page,
            "from_column": from_column_index,
            "number_of_columns_per_page": number_of_columns_per_page,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
        }
