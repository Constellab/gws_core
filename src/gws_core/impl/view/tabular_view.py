# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from gws_core.core.utils.logger import Logger
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view.view_types import ViewType
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view.view import View

if TYPE_CHECKING:
    from gws_core.impl.table.table import Table


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

    _type: ViewType = ViewType.TABULAR

    _table: Table

    # TODO set table not optional
    def __init__(self, table: Table = None, from_row: int = 0, from_column: int = 0,
                 number_of_rows_per_page: int = MAX_NUMBER_OF_ROWS_PER_PAGE,
                 number_of_columns_per_page: int = MAX_NUMBER_OF_COLUMNS_PER_PAGE,
                 replace_nan_by: str = ""):
        super().__init__()

        if table is None:
            Logger.warning("[TabularView] empty construct is deprecated. Use constructor with table instead")

        self._table = table
        self.from_row = from_row
        self.from_column = from_column
        self.number_of_rows_per_page = number_of_rows_per_page
        self.number_of_columns_per_page = number_of_columns_per_page
        self.replace_nan_by = replace_nan_by

    def set_data(
            self, data: DataFrame, row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None):
        Logger.warning("[TabularView] set_data is deprecated. Use constructor instead")

        self._table = Table(data, row_tags=row_tags, column_tags=column_tags)

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
        sub_dataframe = dataframe.iloc[
            safe_from_row:safe_to_row,
            safe_from_column:safe_to_column,
        ]

        # Remove NaN and inf values to convert to json
        replace_nan_by: str = self.replace_nan_by
        if replace_nan_by == "empty":
            replace_nan_by = ""
        data = DataframeHelper.replace_nan_and_inf(sub_dataframe, replace_nan_by)

        return {
            "table": data.to_dict('split')["data"],
            "rows": self._table.get_rows_info(safe_from_row, safe_to_row),
            "columns": self._table.get_columns_info(safe_from_column, safe_to_column),
            "from_row": safe_from_row + 1,  # return 1-based index
            "number_of_rows_per_page": self._get_safe_nb_of_rows_per_page(),
            "from_column": safe_from_column + 1,  # return 1-based index
            "number_of_columns_per_page": self._get_safe_nb_of_columns_per_page(),
            "total_number_of_rows": self._table.nb_rows,
            "total_number_of_columns": self._table.nb_columns,
        }
