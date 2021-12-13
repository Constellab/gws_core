# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Union

from gws_core.config.config_types import ConfigParams
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from ...table.view.table_view import TableView


class DatasetView(TableView):
    """
    Class table view.

    The view model is:
    ```
    {
        "type": "dataset-view",
        "data": dict,
        "targets": dict,
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
    }
    ```
    """

    _type = "dataset-view"
    _data: DataFrame
    _targets: DataFrame

    def _check_and_set_data(self, data: "Dataset", *args, **kwargs):
        from ..dataset import Dataset
        if not isinstance(data, Dataset):
            raise BadRequestException("The data must be a Dataset resource")

        self._data = data.get_features()
        self._targets = data.get_targets()

    def _slice_targets(self, from_row_index: int, to_row_index: int) -> dict:
        n = self._targets.shape[1]
        return self._targets.iloc[from_row_index:to_row_index, 0:n].to_dict('list')

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._data

        # continue ...
        from_row = params.get_value("from_row", 1)
        number_of_rows_per_page = params.get_value("number_of_rows_per_page", TableView.MAX_NUMBERS_OF_ROWS_PER_PAGE)
        from_column = params.get_value("from_column", 1)
        number_of_columns_per_page = params.get_value(
            "number_of_columns_per_page", TableView.MAX_NUMBERS_OF_COLUMNS_PER_PAGE)

        total_number_of_rows = data.shape[0]
        total_number_of_columns = data.shape[1]
        from_row_index = from_row - 1
        from_column_index = from_column - 1
        to_row_index = from_row_index + number_of_rows_per_page
        to_column_index = from_column_index + number_of_columns_per_page

        data = self._slice(
            data,
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index,
        )

        targets = self._slice_targets(
            from_row_index=from_row_index,
            to_row_index=to_row_index,
        )

        return {
            "type": self._type,
            "data": data,
            "targets": targets,
            "from_row": from_row_index,
            "number_of_rows_per_page": number_of_rows_per_page,
            "from_column": from_column_index,
            "number_of_columns_per_page": number_of_columns_per_page,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
        }
