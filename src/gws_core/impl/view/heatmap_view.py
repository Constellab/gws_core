from typing import List

from pandas import DataFrame

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.impl.table.table_types import TableHeaderInfo
from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view.view import View


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
        "rows": List[TableHeaderInfo],
        "columns": List[TableHeaderInfo],
    }
    ```
    """

    _type: ViewType = ViewType.HEATMAP
    _data: DataFrame = None
    _rows_info: List[TableHeaderInfo] = None
    _columns_info: List[TableHeaderInfo] = None

    x_label: str = None
    y_label: str = None

    def set_data(
        self,
        data: DataFrame = None,
        rows_info: List[TableHeaderInfo] = None,
        columns_info: List[TableHeaderInfo] = None,
    ):
        if not isinstance(data, DataFrame):
            raise BadRequestException("The data must be a DataFrame")
        self._data = DataframeHelper.dataframe_to_float(data)
        self._rows_info = rows_info
        self._columns_info = columns_info

    def data_to_dict(self, params: ConfigParams) -> dict:
        if self._data is None:
            raise BadRequestException("No data found")

        data: DataFrame = DataframeHelper.prepare_to_json(self._data, None)

        return {
            "table": NumericHelper.list_2d_to_float(data.values.tolist()),
            "rows": self._rows_info,
            "columns": self._columns_info,
            "x_label": self.x_label,
            "y_label": self.y_label,
        }
