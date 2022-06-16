# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, TypedDict

from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view_types import ViewType
from pandas import DataFrame

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....resource.view import View
from .table_selection import CellRange, TableSelection

if TYPE_CHECKING:
    from ..table import Table


class DataWithTags(TypedDict):
    values: List[Any]
    tags: List[Dict[str, str]]


class BaseTableView(View):
    _type: ViewType
    _table: Table

    def __init__(self, table: Table):
        super().__init__()
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
            if name is not None and name not in self._table.get_data().columns:
                raise BadRequestException(f"The column name '{name}' is not valid")

    def get_values_from_columns(self, column_names: List[str]) -> List[Any]:
        """Get all the values of multiple column flattened
        """
        dataframe = self.get_dataframe_from_columns(column_names)
        return DataframeHelper.flatten_dataframe_by_column(dataframe)

    def get_dataframe_from_columns(self, column_names: List[str]) -> DataFrame:
        """Extract a new dataframe
        """
        self.check_column_names(column_names)
        return self._table.get_data()[column_names]

    def get_values_from_coords(self, ranges: List[CellRange]) -> List[Any]:
        """ Get flattened values from a list of ranges"""

        values: List[Any] = []

        for coord in ranges:
            sub_df = self.get_dataframe_from_coords(coord)

            values += DataframeHelper.flatten_dataframe_by_column(sub_df)

        return values

    def get_dataframe_from_coords(self, range: CellRange) -> DataFrame:
        """ Get a dataframe from a single range"""
        df = self._table.get_data()

        return df.iloc[range.get_from().row: range.get_to().row + 1,
                       range.get_from().column: range.get_to().column + 1]

    def get_values_from_selection_range(self, selection_range: TableSelection) -> List[Any]:
        """Get table flattened value form a SelectionRange
        """

        if selection_range.is_range_selection():
            return self.get_values_from_coords(selection_range.selection)
        else:
            # columns selection
            return self.get_values_from_columns(selection_range.selection)

    def get_row_tags_from_selection_range(self, selection_range: TableSelection) -> List[Dict[str, str]]:

        if selection_range.is_range_selection():
            return self.get_row_tags_from_coords(selection_range.selection)
        else:
            # columns selection
            return self.get_row_tags()

    def get_row_tags_from_coords(self, ranges: List[CellRange]) -> List[Dict[str, str]]:
        tags: List[Dict[str, str]] = []

        for coord in ranges:
            tags += self._table.get_row_tags(from_index=coord.get_from().row, to_index=coord.get_to().row)

        # if all dict are empty, return None to lighten the json
        if all(len(t) == 0 for t in tags):
            return None

        return tags

    def get_row_tags(self) -> List[Dict[str, str]]:
        return self._table.get_row_tags(none_if_empty=True)

        # def get_tags_from_selection_range(self, selection_range: TableSelection) -> List[Dict[str, str]]:
        # """Retrieve row and columns tags of a selection
        # """
        # row_tags = self.get_row_tags_from_selection_range(selection_range)

        # column_tags = self.get_column_tags_from_selection_range(selection_range)

        # print(row_tags)
        # print(column_tags)
        # return row_tags

    # def get_column_tags_from_selection_range(self, selection_range: TableSelection) -> List[Any]:

    #     if selection_range['type'] == 'range':
    #         return self.get_column_tags_from_coords(selection_range['selection'])
    #     else:
    #         # columns selection
    #         return self.get_column_tags(selection_range['selection'])

    # def get_column_tags_from_coords(self, ranges: List[CellRange]) -> List[Dict[str, str]]:
    #     tags: List[Dict[str, str]] = []

    #     for coord in ranges:
    #         tags += self._table.get_column_tags(from_index=coord['from']['column'], to_index=coord['to']['column'] + 1)

    #     return tags

    # def get_column_tags(self, column_names: List[str]) -> List[Dict[str, str]]:
    #     table = self._table.select_by_column_names(column_names)
    #     return table.get_column_tags(none_if_empty=False)

    def get_single_column_tags_from_selection_range(self, selection_range: TableSelection) -> List[Dict[str, str]]:
        if selection_range.is_single_column():
            column_index: int
            if selection_range.is_column_selection():
                column_name = selection_range.selection[0]
                column_index = self._table.get_column_position_from_name(column_name)
            else:
                range: CellRange = selection_range.selection[0]
                column_index = range.get_from().column

            return self._table.get_column_tags(from_index=column_index, to_index=column_index)

        else:
            return None
