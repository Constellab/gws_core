from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Literal

from pandas import DataFrame

from gws_core.core.utils.logger import Logger
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view.view import View

if TYPE_CHECKING:
    from gws_core.impl.table.table import Table

TabularViewSortDirection = Literal["Ascending", "Descending"]


class TabularView(View):
    """
    Use this view to return a section of a Table.
    This view has no parameter and it will not allow pagination to retrieve other rows or columns.

    The view model is:
    ```
    {
        "type": "table-view"
        "title": str,
        "caption": str,
        "data" List[List[float]],
        "rows": List[Dict["name": str, tags: Dict[str, str]]],
        "columns": List[Dict["name": str, tags: Dict[str, str]]],
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
        "sort": {
            "column": str,
            "direction": "Ascending" | "Descending"
        }
    ```
    """

    MAX_NUMBER_OF_ROWS_PER_PAGE = 100
    MAX_NUMBER_OF_COLUMNS_PER_PAGE = 500
    DEFAULT_NUMBER_OF_COLUMNS_PER_PAGE = 250

    from_row: int = 0
    from_column: int = 0
    number_of_rows_per_page: int = MAX_NUMBER_OF_ROWS_PER_PAGE
    number_of_columns_per_page: int = MAX_NUMBER_OF_COLUMNS_PER_PAGE
    replace_nan_by: str = ""
    sort_column: str = None
    sort_direction: TabularViewSortDirection = None

    _type: ViewType = ViewType.TABULAR

    _table: Table = None

    # btyg set table not optional
    def __init__(
        self,
        table: Table,
        from_row: int = 0,
        from_column: int = 0,
        number_of_rows_per_page: int = MAX_NUMBER_OF_ROWS_PER_PAGE,
        number_of_columns_per_page: int = MAX_NUMBER_OF_COLUMNS_PER_PAGE,
        replace_nan_by: str = "",
        sort_column: str = None,
        sort_direction: TabularViewSortDirection = None,
    ):
        super().__init__()

        if table is None:
            raise ValueError("Table is not optional in TabularView")

        self._table = table
        self.from_row = from_row
        self.from_column = from_column
        self.number_of_rows_per_page = number_of_rows_per_page
        self.number_of_columns_per_page = number_of_columns_per_page
        self.replace_nan_by = replace_nan_by
        self.sort_column = sort_column
        self.sort_direction = sort_direction

    def _get_safe_from_row(self) -> int:
        return min(max(self.from_row, 0), self._table.nb_rows - 1)

    def _get_safe_from_column(self) -> int:
        return min(max(self.from_column, 0), self._table.nb_columns - 1)

    def _get_safe_to_row(self) -> int:
        nb_of_rows_per_page = self._get_safe_nb_of_rows_per_page()
        return min(self._get_safe_from_row() + nb_of_rows_per_page, self._table.nb_rows)

    def _get_safe_to_column(self) -> int:
        nb_of_columns_per_page = self._get_safe_nb_of_columns_per_page()
        return min(self._get_safe_from_column() + nb_of_columns_per_page, self._table.nb_columns)

    def _get_safe_nb_of_rows_per_page(self) -> int:
        return min(self.number_of_rows_per_page, self.MAX_NUMBER_OF_ROWS_PER_PAGE)

    def _get_safe_nb_of_columns_per_page(self) -> int:
        return min(self.number_of_columns_per_page, self.MAX_NUMBER_OF_COLUMNS_PER_PAGE)

    def data_to_dict(self, params: ConfigParams) -> dict:
        if self._table is None:
            raise BadRequestException("No table found")

        safe_from_row = self._get_safe_from_row()
        safe_from_column = self._get_safe_from_column()
        safe_to_row = self._get_safe_to_row()
        safe_to_column = self._get_safe_to_column()

        dataframe: DataFrame = self._table.get_data()

        # sort the dataframe if needed
        if self.sort_column is not None:
            dataframe = dataframe.sort_values(
                by=self.sort_column, ascending=self.sort_direction == "Ascending"
            )

        # get the sub dataframe
        sub_dataframe = dataframe.iloc[
            safe_from_row:safe_to_row,
            safe_from_column:safe_to_column,
        ]

        # Remove NaN and inf values to convert to json
        replace_nan_by: str = self.replace_nan_by
        if replace_nan_by == "empty":
            replace_nan_by = ""
        data = DataframeHelper.prepare_to_json(sub_dataframe, replace_nan_by)

        sort = (
            {"column": self.sort_column, "direction": self.sort_direction}
            if self.sort_column is not None
            else None
        )

        total_number_of_rows: int = None
        total_number_of_columns: int = None

        if self._disable_pagination:
            total_number_of_rows = min(self._get_safe_nb_of_rows_per_page(), self._table.nb_rows)
            total_number_of_columns = min(
                self._get_safe_nb_of_columns_per_page(), self._table.nb_columns
            )
        else:
            total_number_of_rows = self._table.nb_rows
            total_number_of_columns = self._table.nb_columns

        return {
            "table": data.to_dict("split")["data"],
            "rows": self._table.get_rows_info(safe_from_row, safe_to_row),
            "columns": self._table.get_columns_info(safe_from_column, safe_to_column),
            "from_row": safe_from_row + 1,  # return 1-based index
            "number_of_rows_per_page": self._get_safe_nb_of_rows_per_page(),
            "from_column": safe_from_column + 1,  # return 1-based index
            "number_of_columns_per_page": self._get_safe_nb_of_columns_per_page(),
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
            "sort": sort,
        }
