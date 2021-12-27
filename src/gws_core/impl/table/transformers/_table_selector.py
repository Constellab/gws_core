# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas
from gws_core.config.config_types import ConfigParams
from pandas import DataFrame

from ....config.param_spec import StrParam
from ....resource.view_types import ViewSpecs
from .base_table_view import BaseTableView

MAX_NUMBERS_OF_ELEMENTS = 1000


class TableView(BaseTableView):
    """
    Class table view.

    This class creates tabular view using a Table.

    The view model is:
    ```
    {
        "type": "table"
        "data": dict,
    }
    ```
    """

    _type = "table-view"
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "rows": StrParam(default_value="R1:R50", human_name=f"Row range (e.g. R1:R50). The max numbers of rows is {MAX_NUMBERS_OF_ELEMENTS}."),
        "columns":
        StrParam(
            default_value="C1:C1000",
            human_name=f"Column range or names (e.g. R5; R10:R20; R35:R38). The max numbers of columns is {MAX_NUMBERS_OF_ELEMENTS}."), }
    _data: DataFrame

    MAX_NUMBERS_OF_ELEMENTS = MAX_NUMBERS_OF_ELEMENTS

    # def _slice(self, data, from_row_index: int, to_row_index: int,
    #            from_column_index: int, to_column_index: int) -> dict:
    #     last_row_index = data.shape[0]
    #     last_column_index = data.shape[1]
    #     from_row_index = min(max(from_row_index, 0), last_row_index-1)
    #     from_column_index = min(max(from_column_index, 0), last_column_index-1)
    #     to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBERS_OF_ROWS_PER_PAGE), last_row_index)
    #     to_column_index = min(
    #         min(to_column_index, from_column_index + self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE),
    #         last_column_index)

    #     # Remove NaN values to convert to json
    #     data: DataFrame = data.fillna('NaN')

    #     return data.iloc[
    #         from_row_index:to_row_index,
    #         from_column_index:to_column_index,
    #     ].to_dict('list')

    def _slice(self, data, rows: str, columns: str) -> dict:
        if not rows:
            rows = data.index[0:TableView.MAX_NUMBERS_OF_ELEMENTS]
        if not columns:
            columns = data.columns[0:TableView.MAX_NUMBERS_OF_ELEMENTS]

        # slice along rows
        data_list = []
        tab = rows.split(";")
        for rng in tab:
            data_list.append(data.iloc[rng, :])
        data = pandas.concat(data_list)

        # slice along colums
        data_list = []
        tab = columns.split(";")
        for rng in tab:
            data_list.append(data.iloc[rng, :])
        data = pandas.concat(data_list)

        # Remove NaN values to convert to json
        data: DataFrame = data.fillna('NaN')

        return data.to_dict('list')

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._data

        rows: int = params.get_value("rows")
        colums: int = params.get_value("columns")

        total_number_of_rows = data.shape[0]
        total_number_of_columns = data.shape[1]

        sliced_data = self._slice(data, rows, columns)

        return {
            **super().to_dict(params),
            "data": sliced_data,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
            "max_number_of_elements": MAX_NUMBERS_OF_ELEMENTS
        }
