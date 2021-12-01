# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.config_types import ConfigParams
from pandas import DataFrame

from ....config.param_spec import IntParam
from ....resource.view_types import ViewSpecs
from ..helper.constructor.data_scale_filter_param import \
    DataScaleFilterParamConstructor
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from .base_table_view import BaseTableView


class TableView(BaseTableView):
    """
    Class table view.

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
        "from_row": IntParam(default_value=1, human_name="From row"),
        "number_of_rows_per_page": IntParam(default_value=50, max_value=100, min_value=1, human_name="Number of rows per page"),
        "from_column": IntParam(default_value=1, human_name="From column"),
        "number_of_columns_per_page": IntParam(default_value=50, max_value=50, min_value=1, human_name="Number of columns per page"),
        "numeric_data_filters": NumericDataFilterParamConstructor.construct_filter(visibility='protected'),
        "text_data_filters": TextDataFilterParamConstructor.construct_filter(visibility='protected'),
        "data_scaling_filters": DataScaleFilterParamConstructor.construct_filter(visibility='protected'),
    }
    _data: DataFrame

    MAX_NUMBERS_OF_ROWS_PER_PAGE = 100
    MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 50

    def _filter_data(self, data, params: ConfigParams):
        data = NumericDataFilterParamConstructor.validate_filter("numeric_data_filters", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_data_filters", data, params)
        data = DataScaleFilterParamConstructor.validate_filter("data_scaling_filters", data, params)
        return data

    def _slice(
            self, data, from_row_index: int = 0, to_row_index: int = 51, from_column_index: int = 0, to_column_index: int = 51) -> dict:
        last_row_index = data.shape[0]
        last_column_index = data.shape[1]
        from_row_index = min(max(from_row_index, 0), last_row_index-1)
        from_column_index = min(max(from_column_index, 0), last_column_index-1)
        to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBERS_OF_ROWS_PER_PAGE), last_row_index)
        to_column_index = min(
            min(to_column_index, from_column_index + self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE),
            last_column_index)

        # Remove NaN values to convert to json
        data: DataFrame = data.fillna('NaN')

        return data.iloc[
            from_row_index:to_row_index,
            from_column_index:to_column_index,
        ].to_dict('list')

    def to_dict(self, params: ConfigParams) -> dict:
        # apply pre-filters
        data = self._data
        data = self._filter_data(data, params)

        # continue ...
        from_row: int = params.get("from_row")
        number_of_rows_per_page: int = params.get("number_of_rows_per_page")
        from_column: int = params.get("from_column")
        number_of_columns_per_page: int = params.get("number_of_columns_per_page")

        total_number_of_rows = data.shape[0]
        total_number_of_columns = data.shape[1]

        from_row_index: int = from_row - 1
        from_column_index: int = from_column - 1
        to_row_index: int = from_row_index + number_of_rows_per_page
        to_column_index: int = from_column_index + number_of_columns_per_page

        data = self._slice(
            data,
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index,
        )

        return {
            **super().to_dict(params),
            "data": data,
            "from_row": from_row_index,
            "number_of_rows_per_page": number_of_rows_per_page,
            "from_column": from_column_index,
            "number_of_columns_per_page": number_of_columns_per_page,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
        }
