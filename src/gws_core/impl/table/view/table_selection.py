# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Literal, Optional, Union


class CellCoord():
    row: int
    column: int

    def __init__(self, row: int, column: int) -> None:
        self.row = row
        self.column = column

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'CellCoord':
        return CellCoord(d['row'], d['column'])


class CellRange():
    _from: CellCoord
    _to: CellCoord

    def __init__(self, from_: CellCoord, to: CellCoord) -> None:
        self._from = from_
        self._to = to

    def get_from(self) -> CellCoord:
        return self._from

    def get_to(self) -> CellCoord:
        return self._to

    def is_single_column(self) -> bool:
        return self._from.column == self._to.column

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'CellRange':
        return CellRange(CellCoord.from_dict(d['from']), CellCoord.from_dict(d['to']))

    @staticmethod
    def from_list(l: List[Dict[str, Any]]) -> List['CellRange']:
        return [CellRange.from_dict(s) for s in l]


class TableSelection():
    """object that represent a TableSelection that can be a range or columns selection

    :param TypedDict: _description_
    :type TypedDict: _type_
    """
    type: Literal['range', 'columns']
    selection: Union[List[CellRange], List[str]]

    def __init__(self, type_: Literal['range', 'columns'], selection: Union[List[CellRange], List[str]]) -> None:
        self.type = type_
        self.selection = selection

    def is_range_selection(self) -> bool:
        return self.type == 'range'

    def is_column_selection(self) -> bool:
        return self.type == 'columns'

    def is_single_column(self) -> bool:
        if self.type == 'columns':
            return len(self.selection) == 1
        else:
            ranges: List[CellRange] = self.selection

            column: int = None

            # check that all ranges are single columns and that they are in the same column
            for range_ in ranges:
                if not range_.is_single_column():
                    return False

                if column is None:
                    column = range_.get_from().column
                else:
                    if column != range_.get_from().column:
                        return False
            return True

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'TableSelection':
        if d['type'] == 'range':
            return TableSelection('range', CellRange.from_list(d['selection']))
        else:
            return TableSelection('columns', d['selection'])


class Serie1d():
    name: str
    y: TableSelection

    def __init__(self, name: str, y: TableSelection) -> None:
        self.name = name
        self.y = y

    def y_is_single_column(self) -> bool:
        return self.y.is_single_column()

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Serie1d':
        return Serie1d(d['name'], TableSelection.from_dict(d['y']))

    @staticmethod
    def from_list(l: List[Dict[str, Any]]) -> List['Serie1d']:
        return [Serie1d.from_dict(d) for d in l]


class Serie2d(Serie1d):
    x: Optional[TableSelection]

    def __init__(self, name: str, y: TableSelection, x: Optional[TableSelection]) -> None:
        super().__init__(name, y)
        self.x = x

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Serie2d':
        x: TableSelection = None
        if 'x' in d and d['x'] is not None:
            x = TableSelection.from_dict(d['x'])
        return Serie2d(d['name'], TableSelection.from_dict(d['y']), x)

    @staticmethod
    def from_list(l: List[Dict[str, Any]]) -> List['Serie2d']:
        return [Serie2d.from_dict(d) for d in l]
