
from gws_core.config.param_spec import IntParam
from gws_core.core.classes.paginator import PageInfo
from gws_core.resource.view_types import ViewSpecs
from pandas import DataFrame

from .base_table_view import BaseTableView


class TableView(BaseTableView):
    """
    Class table view.

    The view model is:
    ```
    {
        "type": "table-view"
        "data": dict
    }
    ```
    """

    _type = "table-view"
    _specs: ViewSpecs = {
        "row_page": IntParam(default_value=1, human_name="Row page number"),
        "row_page_size": IntParam(default_value=50, max_value=50, min_value=1, human_name="Number of rows per page"),
        "column_page": IntParam(default_value=1, human_name="Row page number"),
        "column_page_size": IntParam(default_value=50, max_value=50, min_value=1, human_name="Number of columns per page")
    }
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

    def to_dict(self, row_page: int = 1, row_page_size: int = 50, column_page: int = 1,
                column_page_size: int = 50) -> dict:

        total_number_of_rows = self._data.shape[0]
        total_number_of_columns = self._data.shape[1]

        row_page_info: PageInfo = PageInfo(row_page, row_page_size,
                                           total_number_of_rows, self.MAX_NUMBERS_OF_ROWS_PER_PAGE, 1)
        column_page_info: PageInfo = PageInfo(column_page, column_page_size,
                                              total_number_of_columns, self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE, 1)

        table = self._slice(
            from_row_index=row_page_info.from_index,
            to_row_index=row_page_info.to_index,
            from_column_index=column_page_info.from_index,
            to_column_index=column_page_info.to_index
        )

        return {
            "type": self._type,
            "data": table,
            "row_page": row_page,
            "number_of_rows_per_page": row_page_size,
            "column_page": column_page,
            "number_of_columns_per_page": column_page_size,
            "from_row_index": row_page_info.from_index,
            "to_row_index": row_page_info.to_index,
            "total_number_of_rows": total_number_of_rows,
            "from_column_index": column_page_info.from_index,
            "to_column_index": column_page_info.to_index,
            "total_number_of_columns": total_number_of_columns,
        }
