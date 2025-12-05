from enum import Enum
from typing import Literal

from typing_extensions import TypedDict


class TableColumnType(Enum):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    OBJECT = "OBJECT"


class TableHeaderInfo(TypedDict):
    """Object to represent the information about a table header (row, column)"""

    name: str
    tags: dict[str, str]


class TableColumnInfo(TableHeaderInfo):
    type: TableColumnType


AxisType = Literal[0, 1, "index", "columns"]


def is_row_axis(axis: AxisType) -> bool:
    return axis in [0, "index"]
