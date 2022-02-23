# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View
from .tabular_view import TabularView


class HeatmapView(View):
    """
    TableHistogramView

    Class for creating heatmaps using a DataFrame table.

    The view model is:
    ------------------

    ```
    {
        "type": "heatmap-view",
        "title": str,
        "caption": str,
        "data": {'column_name_1': List, 'column_name_2: List, ...},
        "row_names": List[str],
        "row_tags": List[Dict[str, str]],
        "column_tags": List[Dict[str, str]],
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
    }
    ```
    """

    MAX_NUMBER_OF_ROWS_PER_PAGE = TabularView.MAX_NUMBER_OF_ROWS_PER_PAGE
    MAX_NUMBER_OF_COLUMNS_PER_PAGE = TabularView.MAX_NUMBER_OF_COLUMNS_PER_PAGE

    from_row: int = 1
    from_column: int = 1
    number_of_rows_per_page: int = MAX_NUMBER_OF_ROWS_PER_PAGE
    number_of_columns_per_page: int = MAX_NUMBER_OF_COLUMNS_PER_PAGE

    _type: str = "heatmap-view"
    _data: DataFrame = None
    _row_tags: List[Dict[str, str]] = None
    _column_tags: List[Dict[str, str]] = None

    def set_data(
            self, *, data: DataFrame = None, row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None):
        if not isinstance(data, DataFrame):
            raise BadRequestException("The data must be a DataFrame")
        self._data = data
        self._row_tags = row_tags
        self._column_tags = column_tags

    def to_dict(self, params: ConfigParams) -> dict:
        if self._data is None:
            self._data = DataFrame()

        helper_view = TabularView()
        helper_view.set_data(self._data, row_tags=self._row_tags, column_tags=self._column_tags)
        helper_view.from_row = self.from_row
        helper_view.from_column = self.from_column
        helper_view.number_of_rows_per_page = self.number_of_rows_per_page
        helper_view.number_of_columns_per_page = self.number_of_columns_per_page
        helper_view.replace_nan_by = ""

        view_dict = helper_view.to_dict(params)
        view_dict["type"] = self._type
        return view_dict
