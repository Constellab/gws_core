# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import (TYPE_CHECKING, Any, Dict, List, Literal, Optional,
                    TypedDict, Union)

from pandas import DataFrame

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....resource.view import View

if TYPE_CHECKING:
    from ..table import Table


class CellCoord(TypedDict):
    row: int
    column: int


class CellCoords(TypedDict):
    from_: CellCoord
    to: CellCoord


class SelectionRange(TypedDict):
    type: Literal['range', 'columns']
    selection: Union[List[CellCoords], List[str]]


class Serie1d(TypedDict):
    name: str
    y: SelectionRange


class Serie2d(Serie1d):
    x: Optional[SelectionRange]


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
            if name is not None and name not in self._table.get_data().columns:
                raise BadRequestException(f"The column name '{name}' is not valid")

    def get_column_values_as_list(self, column_names: List[str]) -> List[Any]:
        """Get all the values of multiple column flatten

        :param column_names: _description_
        :type column_names: List[str]
        :return: _description_
        :rtype: List[Any]
        """
        dataframe = self.get_dataframe_from_columns(column_names)
        return self.flatten_dataframe_by_column(dataframe)

    def get_dataframe_from_columns(self, column_names: List[str]) -> DataFrame:
        self.check_column_names(column_names)
        return self._table.get_data[column_names]

    def get_values_from_coords(self, coords: List[CellCoords]) -> List[Any]:

        values: List[float] = []

        for coord in coords:
            sub_df = self.get_dataframe_from_coords(coord)

            values += self.flatten_dataframe_by_column(sub_df)

        return values

    def get_dataframe_from_coords(self, coords: List[CellCoords]) -> DataFrame:
        df = self._table.get_data()

        return df.iloc[coords['from']['row']: coords['to']['row'] + 1,
                       coords['from']['column']: coords['to']['column'] + 1]

    def get_selection_range_values(self, selection_range: SelectionRange) -> List[Any]:

        if selection_range['type'] == 'range':
            return self.get_values_from_coords(selection_range['selection'])
        else:
            # columns selection
            return self.get_column_values_as_list(selection_range['selection'])

    def get_row_tags_from_selection_range(self, selection_range: SelectionRange) -> List[Any]:

        if selection_range['type'] == 'range':
            return self.get_row_tags_from_coords(selection_range['selection'])
        else:
            # columns selection
            return self.get_row_tags()

    def get_row_tags_from_coords(self, coords: List[CellCoords]) -> List[Dict[str, str]]:
        tags: List[Dict[str, str]] = []

        for coord in coords:
            tags += self._table.get_row_tags(from_index=coord['from']['row'], to_index=coord['to']['row'] + 1)

        # if all dict are empty, return None to lighten the json
        if all(len(t) == 0 for t in tags):
            return None

        return tags

    def get_row_tags(self) -> List[Dict[str, str]]:
        return self._table.get_row_tags(none_if_empty=True)
