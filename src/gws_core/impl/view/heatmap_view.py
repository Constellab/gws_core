# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.impl.table.table_helper import TableHelper
from gws_core.impl.table.table_types import TableHeaderInfo
from numpy import nan
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View


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
        "data" List[List[float]],
        "rows": TableHeaderInfo,
        "columns": TableHeaderInfo,
    }
    ```
    """

    _type: str = "heatmap-view"
    _data: DataFrame = None
    _rows_info: TableHeaderInfo = None
    _columns_info: TableHeaderInfo = None

    def set_data(
            self, data: DataFrame = None, rows_info: TableHeaderInfo = None, columns_info: TableHeaderInfo = None):
        if not isinstance(data, DataFrame):
            raise BadRequestException("The data must be a DataFrame")
        self._data = TableHelper.dataframe_to_float(data)
        self._rows_info = rows_info
        self._columns_info = columns_info

    def to_dict(self, params: ConfigParams) -> dict:
        if self._data is None:
            raise BadRequestException("No data found")

        return {
            "type": self._type,
            "data": self._data.replace({nan: None}).values.tolist(),
            "rows": self._rows_info,
            "columns": self._columns_info
        }
