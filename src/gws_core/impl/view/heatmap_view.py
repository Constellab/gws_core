# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

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
        "rows": List[Dict["name": str, tags: Dict[str, str]]],
        "columns": List[Dict["name": str, tags: Dict[str, str]]],
    }
    ```
    """

    _type: str = "heatmap-view"
    _data: DataFrame = None
    _row_tags: List[Dict[str, str]] = None
    _column_tags: List[Dict[str, str]] = None

    def set_data(
            self, data: DataFrame = None, row_tags: List[Dict[str, str]] = None, column_tags: List[Dict[str, str]] = None):
        if not isinstance(data, DataFrame):
            raise BadRequestException("The data must be a DataFrame")
        self._data = self.dataframe_to_float(data)
        self._row_tags = row_tags
        self._column_tags = column_tags

    def to_dict(self, params: ConfigParams) -> dict:
        if self._data is None:
            raise BadRequestException("No data found")

        return {
            "type": self._type,
            "data": self._data.replace({nan: None}).values.tolist(),
            "rows": self._row_tags,
            "columns": self._column_tags
        }
