from typing import List, Union, TYPE_CHECKING

from pandas import DataFrame

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from .base_table_view import BaseTableView

class TableView(BaseTableView):
    """
    Class table view.

    The view model is:
    ```
    {
        "type": "table-view"
        "title": str
        "subtitle": str
        "data": dict
    }
    ```
    """

    _type = "table-view"
    _data: DataFrame

    MAX_NUMBERS_OF_ROWS_PER_PAGE = 50
    MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 50

    def _slice(self, from_row_index: int = 0, to_row_index: int = 49, from_column_index: int = 0, to_column_index: int = 49) -> dict:
        last_row_index = self._data.shape[0] - 1
        last_column_index = self._data.shape[1] - 1
        from_row_index = min(max(from_row_index, 0), last_row_index)
        from_column_index = min(max(from_column_index, 0), last_column_index)
        to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBERS_OF_ROWS_PER_PAGE), last_row_index)
        to_column_index = min(
            min(to_column_index, from_column_index + self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE),
            last_column_index)

        table = self._data.iloc[
            from_row_index:to_row_index,
            from_column_index:to_column_index,
        ].to_dict()

        return table

    def to_dict(self, row_page: int = 1, number_of_rows_per_page: int = 50, column_page: int = 1,
                number_of_columns_per_page: int = 50, title: str = None, subtitle: str = None) -> dict:
        number_of_rows_per_page = min(self.MAX_NUMBERS_OF_ROWS_PER_PAGE, number_of_rows_per_page)
        number_of_columns_per_page = min(self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE, number_of_columns_per_page)

        from_row_index = (row_page-1)*number_of_rows_per_page
        to_row_index = from_row_index + number_of_rows_per_page
        from_column_index = (column_page-1)*number_of_columns_per_page
        to_column_index = from_column_index + number_of_columns_per_page

        table = self._slice(
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index
        )

        total_number_of_rows = self._data.shape[0]
        total_number_of_columns = self._data.shape[1]

        return {
            "type": self._type,
            "title": title,
            "subtitle": subtitle,
            "data": table,
            "row_page": row_page,
            "number_of_rows_per_page": number_of_rows_per_page,
            "column_page": column_page,
            "number_of_columns_per_page": number_of_columns_per_page,
            "from_row_index": from_row_index,
            "to_row_index": to_row_index,
            "total_number_of_rows": total_number_of_rows,
            "from_column_index": from_column_index,
            "to_column_index": to_column_index,
            "total_number_of_columns": total_number_of_columns,
            "current_sheet": 0,
            "total_number_of_sheets": 0
        }
