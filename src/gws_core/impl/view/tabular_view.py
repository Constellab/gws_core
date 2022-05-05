# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from gws_core.resource.view_types import ViewType
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View


class TabularView(View):
    """
    Class table view.

    This class creates tabular view using a DataFrame table.

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
    MAX_NUMBER_OF_COLUMNS_PER_PAGE = 100

    from_row: int = 1
    from_column: int = 1
    number_of_rows_per_page: int = MAX_NUMBER_OF_ROWS_PER_PAGE
    number_of_columns_per_page: int = MAX_NUMBER_OF_COLUMNS_PER_PAGE
    replace_nan_by: str = ""

    _type: ViewType = ViewType.TABLE
    _data: DataFrame = None
    _row_tags: List[Dict[str, str]] = None
    _column_tags: List[Dict[str, str]] = None

    def set_data(
            self, data: DataFrame, row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None):
        if not isinstance(data, DataFrame):
            raise BadRequestException("The data must be a DataFrame")
        self._data = data
        self._set_row_tags(row_tags)
        self._set_column_tags(column_tags)

    def _set_row_tags(self, row_tags: List[Dict[str, str]]):
        if row_tags is None:
            self._row_tags = [{}] * self._data.shape[0]
            return

        if not isinstance(row_tags, list):
            raise BadRequestException("The row_tags must be a list")
        if len(row_tags) != self._data.shape[0]:
            raise BadRequestException("The length of row_tags must be equal to the number of rows in data")

        try:
            row_tags = [{str(k): str(v) for k, v in t.items()} for t in row_tags]
        except Exception as err:
            raise BadRequestException(
                "The row_tags cannot be cleaned. Please check that row_tags is a list of dict") from err
        self._row_tags = row_tags

    def _set_column_tags(self, column_tags: List[Dict[str, str]]):
        if column_tags is None:
            self._column_tags = [{}] * self._data.shape[1]
            return

        if not isinstance(column_tags, list):
            raise BadRequestException("The column_tags must be a list")
        if len(column_tags) != self._data.shape[1]:
            raise BadRequestException("The length of column_tags must be equal to the number of columns in data")

        try:
            column_tags = [{str(k): str(v) for k, v in t.items()} for t in column_tags]
        except Exception as err:
            raise BadRequestException(
                "The column_tags cannot be cleaned. Please check that column_tags is a list of dict") from err
        self._column_tags = column_tags

    def _slice(self, from_row_index: int, to_row_index: int,
               from_column_index: int, to_column_index: int) -> dict:
        last_row_index = self._data.shape[0]
        last_column_index = self._data.shape[1]
        from_row_index = min(max(from_row_index, 0), last_row_index-1)
        from_column_index = min(max(from_column_index, 0), last_column_index-1)
        to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBER_OF_ROWS_PER_PAGE), last_row_index)
        to_column_index = min(
            min(to_column_index, from_column_index + self.MAX_NUMBER_OF_COLUMNS_PER_PAGE),
            last_column_index)

        sliced_data = self._data.iloc[
            from_row_index:to_row_index,
            from_column_index:to_column_index,
        ]
        sliced_row_tags = self._row_tags[from_row_index:to_row_index]
        sliced_column_tags = self._column_tags[from_column_index:to_column_index]
        sliced_data_info = {
            "data": sliced_data,
            "row_tags": sliced_row_tags,
            "column_tags": sliced_column_tags,
            "indexes": (from_row_index, to_row_index, from_column_index, to_column_index,)
        }
        return sliced_data_info

    def data_to_dict(self, params: ConfigParams) -> dict:
        if self._data is None:
            raise BadRequestException("No data found")

        # continue ...
        from_row: int = params.get("from_row", self.from_row)
        number_of_rows_per_page: int = params.get("number_of_rows_per_page", self.number_of_rows_per_page)
        from_column: int = params.get("from_column", self.from_column)
        number_of_columns_per_page: int = params.get("number_of_columns_per_page", self.number_of_columns_per_page)

        total_number_of_rows = self._data.shape[0]
        total_number_of_columns = self._data.shape[1]

        from_row_index: int = from_row - 1
        from_column_index: int = from_column - 1
        to_row_index: int = from_row_index + number_of_rows_per_page
        to_column_index: int = from_column_index + number_of_columns_per_page

        sliced_data_info = self._slice(
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index)

        data = sliced_data_info["data"]
        row_tags = sliced_data_info["row_tags"]
        column_tags = sliced_data_info["column_tags"]
        from_row_index, to_row_index, from_column_index, to_column_index = sliced_data_info["indexes"]

        # Remove NaN values to convert to json
        replace_nan_by: str = params.get("replace_nan_by", self.replace_nan_by)
        if replace_nan_by == "empty":
            replace_nan_by = ""
        data: DataFrame = data.fillna(replace_nan_by)

        data_dict = data.to_dict('split')
        rows = [{"name": name, "tags": row_tags[i]} for i, name in enumerate(data_dict["index"])]
        columns = [{"name": name, "tags": column_tags[i]} for i, name in enumerate(data_dict["columns"])]

        return {
            "table": data_dict["data"],
            "rows": rows,
            "columns": columns,
            "from_row": from_row_index,
            "number_of_rows_per_page": number_of_rows_per_page,
            "from_column": from_column_index,
            "number_of_columns_per_page": number_of_columns_per_page,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
        }
