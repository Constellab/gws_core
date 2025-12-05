from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pandas import DataFrame
from typing_extensions import TypedDict

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view.view_types import ViewType

from ....core.exception.exceptions.bad_request_exception import BadRequestException
from ....resource.view.view import View
from .table_selection import CellRange, Serie1dList, TableSelection

if TYPE_CHECKING:
    from ..table import Table


class DataWithTags(TypedDict):
    values: list[Any]
    tags: list[dict[str, str]]


class BaseTableView(View):
    _type: ViewType
    _table: Table

    # Spec to define the name of the x and y axis
    _2d_axis_labels_specs = ConfigSpecs(
        {
            "x_axis_label": StrParam(optional=True),
            "y_axis_label": StrParam(optional=True),
        }
    )

    def __init__(self, table: Table):
        super().__init__()
        self._check_and_set_data(table)

    def _check_and_set_data(self, table: Table):
        from ..table import Table

        if table is None:
            raise BadRequestException("The provided table cannot be None")

        if not isinstance(table, Table):
            raise BadRequestException("The data must be a Table resource")
        self._table = table

    def get_table(self):
        return self._table

    def check_column_names(self, column_names):
        for name in column_names:
            if name is not None and name not in self._table.get_data().columns:
                raise BadRequestException(f"The column name '{name}' is not valid")

    def get_values_from_columns(self, column_names: list[str]) -> list[Any]:
        """Get all the values of multiple column flattened"""
        dataframe = self.get_dataframe_from_columns(column_names)
        return DataframeHelper.flatten_dataframe_by_column(dataframe)

    def get_dataframe_from_columns(self, column_names: list[str]) -> DataFrame:
        """Extract a new dataframe"""
        self.check_column_names(column_names)
        return self._table.get_data()[column_names]

    def get_values_from_coords(self, ranges: list[CellRange]) -> list[Any]:
        """Get flattened values from a list of ranges"""

        values: list[Any] = []

        for coord in ranges:
            sub_df = self.get_dataframe_from_coords(coord)

            values += DataframeHelper.flatten_dataframe_by_column(sub_df)

        return values

    def get_dataframe_from_coords(self, range: CellRange) -> DataFrame:
        """Get a dataframe from a single range"""
        df = self._table.get_data()

        return df.iloc[
            range.get_from().row : range.get_to().row + 1,
            range.get_from().column : range.get_to().column + 1,
        ]

    def get_values_from_selection_range(self, selection_range: TableSelection) -> list[Any]:
        """Get table flattened value form a SelectionRange"""

        if selection_range.is_range_selection():
            return self.get_values_from_coords(selection_range.selection)
        else:
            # columns selection
            return self.get_values_from_columns(selection_range.selection)

    def get_row_tags_from_selection_range(
        self, selection_range: TableSelection
    ) -> list[dict[str, str]]:
        if selection_range.is_range_selection():
            return self.get_row_tags_from_coords(selection_range.selection)
        else:
            # columns selection
            return self.get_row_tags()

    def get_row_tags_from_coords(self, ranges: list[CellRange]) -> list[dict[str, str]]:
        tags: list[dict[str, str]] = []

        for coord in ranges:
            tags += self._table.get_row_tags(
                from_index=coord.get_from().row, to_index=coord.get_to().row
            )

        # if all dict are empty, return None to lighten the json
        if all(len(t) == 0 for t in tags):
            return None

        return tags

    def get_row_tags(self) -> list[dict[str, str]]:
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

    def get_single_column_tags_from_selection_range(
        self, selection_range: TableSelection
    ) -> list[dict[str, str]]:
        if selection_range.is_single_column():
            column_index: int
            if selection_range.is_column_selection():
                column_name = selection_range.selection[0]
                column_index = self._table.get_column_index_from_name(column_name)
            else:
                range: CellRange = selection_range.selection[0]
                column_index = range.get_from().column

            return self._table.get_column_tags(from_index=column_index, to_index=column_index)

        else:
            return None

    def get_x_tick_labels_from_series_list(self, serie_list: Serie1dList) -> list[str] | None:
        """Get the x tick labels from a serie list if possible, if all the series have the same
        rows selection"""

        # all the y series must have the same row selection
        if serie_list.all_y_series_have_same_row_selection():
            # if they all are column selection, the tick labels are all the row names
            if serie_list.all_y_are_column_selection():
                return self.get_table().get_row_names()
            else:
                # otherwise, take the first serie row selection as they all have the same selection
                cell_range: list[CellRange] = serie_list.series[0].y.selection

                x_tick_labels = []
                # retrieve all the row names based on the row selection
                for cell in cell_range:
                    x_tick_labels += self.get_table().get_row_names(
                        cell.get_from().row, cell.get_to().row + 1
                    )

                return x_tick_labels

        return None
