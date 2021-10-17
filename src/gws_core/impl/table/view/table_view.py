import numpy
import pandas
from pandas import DataFrame

from ....config.param_spec import IntParam, StrParam
from ....core.classes.paginator import PageInfo
from ....resource.view_types import ViewSpecs

from .base_table_view import BaseTableView


class TableView(BaseTableView):
    """
    Class table view.

    The view model is:
    ```
    {
        "type": "table"
        "title": str,
        "subtitle": str,
        "data": dict,
    }
    ```
    """

    _type = "table"
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "from_row": IntParam(default_value=1, human_name="From row"),
        "number_of_rows_per_page": IntParam(default_value=50, max_value=100, min_value=1, human_name="Number of rows per page"),
        "from_column": IntParam(default_value=1, human_name="From column"),
        "number_of_columns_per_page": IntParam(default_value=50, max_value=50, min_value=1, human_name="Number of columns per page"),
        "scale": StrParam(default_value=None, optional=True, allowed_values=["log10", "log2"], visibility='protected', human_name="Scaling factor to apply"),
    }
    _data: DataFrame

    MAX_NUMBERS_OF_ROWS_PER_PAGE = 100
    MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 50
    
    def _slice(self, data, from_row_index: int = 0, to_row_index: int = 51, from_column_index: int = 0, to_column_index: int = 51, scale: str = None) -> dict:
        last_row_index = data.shape[0]
        last_column_index = data.shape[1]
        from_row_index = min(max(from_row_index, 0), last_row_index-1)
        from_column_index = min(max(from_column_index, 0), last_column_index-1)
        to_row_index = min(min(to_row_index, from_row_index + self.MAX_NUMBERS_OF_ROWS_PER_PAGE), last_row_index)
        to_column_index = min(
            min(to_column_index, from_column_index + self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE),
            last_column_index)

        if scale:
            data = data.apply(pandas.to_numeric,errors='coerce')
            if scale == "log10":
                data = DataFrame(data=numpy.log10(data.values), index=data.index, columns=data.columns)
            elif scale == "log2":
                data = DataFrame(data=numpy.log2(data.values), index=data.index, columns=data.columns)
      
        # Remove NaN values to convert to json
        # data_frame: DataFrame = data.fillna('NaN')
         
        return data.iloc[
            from_row_index:to_row_index,
            from_column_index:to_column_index,
        ].to_dict('list')

    def _slice_data(self, from_row_index: int = 0, to_row_index: int = 51, from_column_index: int = 0, to_column_index: int = 51, scale: str = None) -> dict:
        return self._slice(
            self._data, 
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index,
            scale=scale
        )

    def to_dict(self, from_row: int = 1, number_of_rows_per_page: int = 50, from_column: int = 1,
                number_of_columns_per_page: int = 50, scale: str = None, **kwargs) -> dict:

        total_number_of_rows = self._data.shape[0]
        total_number_of_columns = self._data.shape[1]

        from_row_index = from_row - 1
        from_column_index = from_column - 1
        to_row_index = from_row_index + number_of_rows_per_page
        to_column_index = from_column_index + number_of_columns_per_page

        data = self._slice_data(
            from_row_index=from_row_index,
            to_row_index=to_row_index,
            from_column_index=from_column_index,
            to_column_index=to_column_index,
            scale=scale
        )

        return {
            **super().to_dict(**kwargs),
            "data": data,
            "from_row": from_row_index,
            "number_of_rows_per_page": number_of_rows_per_page,
            "from_column": from_column_index,
            "number_of_columns_per_page": number_of_columns_per_page,
            "total_number_of_rows": total_number_of_rows,
            "total_number_of_columns": total_number_of_columns,
        }

    # def to_dict(self, row_page: int = 1, row_page_size: int = 50, column_page: int = 1,
    #             column_page_size: int = 50) -> dict:

    #     total_number_of_rows = self._data.shape[0]
    #     total_number_of_columns = self._data.shape[1]

    #     row_page_info: PageInfo = PageInfo(row_page, row_page_size,
    #                                        total_number_of_rows, self.MAX_NUMBERS_OF_ROWS_PER_PAGE, 1)
    #     column_page_info: PageInfo = PageInfo(column_page, column_page_size,
    #                                           total_number_of_columns, self.MAX_NUMBERS_OF_COLUMNS_PER_PAGE, 1)

    #     table = self._slice_data(
    #         from_row_index=row_page_info.from_index,
    #         to_row_index=row_page_info.to_index,
    #         from_column_index=column_page_info.from_index,
    #         to_column_index=column_page_info.to_index
    #     )

    #     return {
    #         "type": self._type,
    #         "data": table,
    #         "row_page": row_page,
    #         "number_of_rows_per_page": row_page_size,
    #         "column_page": column_page,
    #         "number_of_columns_per_page": column_page_size,
    #         "from_row_index": row_page_info.from_index,
    #         "to_row_index": row_page_info.to_index,
    #         "total_number_of_rows": total_number_of_rows,
    #         "from_column_index": column_page_info.from_index,
    #         "to_column_index": column_page_info.to_index,
    #         "total_number_of_columns": total_number_of_columns,
    #     }
