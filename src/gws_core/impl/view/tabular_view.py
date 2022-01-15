# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


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
        "type": "table"
        "title": str,
        "caption": str,
        "data": {'column_name_1': list, 'column_name_2: list, ...},
        "row_names": list
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
    }
    ```
    """

    MAX_NUMBER_OF_ROWS_PER_PAGE = 5000
    MAX_NUMBER_OF_COLUMNS_PER_PAGE = 99

    from_row: int = 1
    from_column: int = 1
    number_of_rows_per_page: int = MAX_NUMBER_OF_ROWS_PER_PAGE
    number_of_columns_per_page: int = MAX_NUMBER_OF_COLUMNS_PER_PAGE
    replace_nan_by: str = ""

    _type = "table-view"
    _data: DataFrame = None

    def set_data(self, data: DataFrame):
        if not isinstance(data, DataFrame):
            raise BadRequestException("The data must be a DataFrame")
        self._data = data

    def _slice(self, data: DataFrame, from_row_index: int, to_row_index: int,
               from_column_index: int, to_column_index: int, replace_nan_by: str = "") -> dict:
        last_row_index = data.shape[0]
        last_column_index = data.shape[1]
        from_row_index = min(max(from_row_index, 0), last_row_index-1)
        from_column_index = min(max(from_column_index, 0), last_column_index-1)
        to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBER_OF_ROWS_PER_PAGE), last_row_index)
        to_column_index = min(
            min(to_column_index, from_column_index + self.MAX_NUMBER_OF_COLUMNS_PER_PAGE),
            last_column_index)

        # Remove NaN values to convert to json
        data: DataFrame = data.fillna(replace_nan_by)

        return data.iloc[
            from_row_index:to_row_index,
            from_column_index:to_column_index,
        ].to_dict('list')

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._data
        if data is None:
            data = DataFrame()

        # continue ...
        from_row: int = self.from_row
        number_of_rows_per_page: int = self.number_of_rows_per_page
        from_column: int = self.from_column
        number_of_columns_per_page: int = self.number_of_columns_per_page
        replace_nan_by: str = self.replace_nan_by
        if replace_nan_by == "empty":
            replace_nan_by = ""

        total_number_of_rows = data.shape[0]
        total_number_of_columns = data.shape[1]

        from_row_index: int = from_row - 1
        from_column_index: int = from_column - 1
        to_row_index: int = from_row_index + number_of_rows_per_page
        to_column_index: int = from_column_index + number_of_columns_per_page

        data_list = self._slice(
            data,
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index,
            replace_nan_by=replace_nan_by)

        return {
            **super().to_dict(params),
            "data": data_list,
            "row_names": data.index.tolist(),
            "from_row": from_row_index,
            "number_of_rows_per_page": number_of_rows_per_page,
            "from_column": from_column_index,
            "number_of_columns_per_page": number_of_columns_per_page,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
        }
