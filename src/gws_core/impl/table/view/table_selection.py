from typing import Any, Literal


class CellCoord:
    row: int
    column: int

    def __init__(self, row: int, column: int) -> None:
        self.row = row
        self.column = column

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "CellCoord":
        return CellCoord(d["row"], d["column"])


class CellRange:
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

    def is_same_rows(self, other: "CellRange") -> bool:
        """Check that two cell ranges have the same rows"""
        return self._from.row == other._from.row and self._to.row == other._to.row

    @staticmethod
    def from_dict(dict_: dict[str, Any]) -> "CellRange":
        return CellRange(CellCoord.from_dict(dict_["from"]), CellCoord.from_dict(dict_["to"]))

    @staticmethod
    def from_list(list_: list[dict[str, Any]]) -> list["CellRange"]:
        return [CellRange.from_dict(s) for s in list_]


class TableSelection:
    """object that represent a TableSelection that can be a range or columns selection

    :param TypedDict: _description_
    :type TypedDict: _type_
    """

    type: Literal["range", "columns"]
    selection: list[CellRange] | list[str]

    def __init__(
        self, type_: Literal["range", "columns"], selection: list[CellRange] | list[str]
    ) -> None:
        self.type = type_
        self.selection = selection

    def is_range_selection(self) -> bool:
        return self.type == "range"

    def is_column_selection(self) -> bool:
        return self.type == "columns"

    def is_single_column(self) -> bool:
        if self.type == "columns":
            return len(self.selection) == 1
        else:
            ranges: list[CellRange] = self.selection

            column: int = None

            # check that all ranges are single columns and that they are in the same column
            for range_ in ranges:
                if not range_.is_single_column():
                    return False

                if column is None:
                    column = range_.get_from().column
                elif column != range_.get_from().column:
                    return False
            return True

    def is_same_row_selection(self, other: "TableSelection") -> bool:
        """Method to check if the selection has the same row selections as another selection"""
        if self.type != other.type:
            return False

        # if both are column selection they retrieve all rows so are the same
        if self.is_column_selection() and other.is_column_selection():
            return True

        # if both are range selection we check that they are in the same row
        ranges: list[CellRange] = self.selection
        other_ranges: list[CellRange] = other.selection

        if len(ranges) != len(other_ranges):
            return False

        for i in range(len(ranges)):
            # check that for each range the from and to rows are the same
            if not ranges[i].is_same_rows(other_ranges[i]):
                return False

        return True

    def get_name(self) -> str | None:
        """Method to return a possible name of the selection (only if selection by columns)

        :return: _description_
        :rtype: Optional[str]
        """
        if self.type == "columns":
            return " ".join(self.selection)
        else:
            return None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "TableSelection":
        if d["type"] == "range":
            return TableSelection("range", CellRange.from_list(d["selection"]))
        else:
            return TableSelection("columns", d["selection"])


class Serie1d:
    name: str
    y: TableSelection

    def __init__(self, name: str, y: TableSelection) -> None:
        self.name = name
        self.y = y

    def y_is_column_selection(self) -> bool:
        return self.y.is_column_selection()

    def y_is_single_column(self) -> bool:
        return self.y.is_single_column()

    def get_y_selection_name(self) -> str | None:
        return self.y.get_name()

    @staticmethod
    def from_dict(dict_: dict[str, Any]) -> "Serie1d":
        return Serie1d(dict_["name"], TableSelection.from_dict(dict_["y"]))

    @staticmethod
    def from_list(list_: list[dict[str, Any]]) -> list["Serie1d"]:
        return [Serie1d.from_dict(d) for d in list_]


class Serie2d(Serie1d):
    x: TableSelection | None

    def __init__(self, name: str, y: TableSelection, x: TableSelection | None) -> None:
        super().__init__(name, y)
        self.x = x

    def get_x_selection_name(self) -> str | None:
        return self.x.get_name() if self.x else None

    @staticmethod
    def from_dict(dict_: dict[str, Any]) -> "Serie2d":
        x: TableSelection = None
        if "x" in dict_ and dict_["x"] is not None:
            x = TableSelection.from_dict(dict_["x"])
        return Serie2d(dict_["name"], TableSelection.from_dict(dict_["y"]), x)

    @staticmethod
    def from_list(list_: list[dict[str, Any]]) -> list["Serie2d"]:
        return [Serie2d.from_dict(d) for d in list_]


class Serie1dList:
    """object that represent a list of Serie1d"""

    series: list[Serie1d]

    def __init__(self, series: list[Serie1d]) -> None:
        self.series = series

    def all_y_series_have_same_row_selection(self) -> bool:
        first_serie = self.series[0]

        for serie in self.series[1:]:
            if not first_serie.y.is_same_row_selection(serie.y):
                return False

        return True

    def all_y_are_column_selection(self) -> bool:
        return all([serie.y_is_column_selection() for serie in self.series])

    def all_y_are_range_selection(self) -> bool:
        return all([serie.y.is_range_selection() for serie in self.series])

    def __len__(self) -> int:
        return len(self.series)

    @staticmethod
    def from_list(list_: list[dict[str, Any]]) -> "Serie1dList":
        return Serie1dList(Serie1d.from_list(list_))
