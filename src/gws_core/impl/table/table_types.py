# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import Dict, List, Literal, TypedDict


class TableColumnType(Enum):
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    STRING = 'STRING'
    BOOLEAN = 'BOOLEAN'
    OBJECT = 'OBJECT'


class TableHeaderInfo(TypedDict):
    """Object to represent the information about a table header (row, column)
    """
    name: str
    tags: Dict[str, str]


class TableColumnInfo(TableHeaderInfo):
    type: TableColumnType


# TODO remove meta on version 0.3.15
class TableMeta(TypedDict):
    """ Object that represent the table Meta information
    """
    row_tags: List[Dict[str, str]]
    column_tags: List[Dict[str, str]]


AxisType = Literal[0, 1, "index", "columns"]


def is_row_axis(axis: AxisType) -> bool:
    return axis in [0, "index"]
