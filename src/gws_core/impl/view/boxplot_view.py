# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
from typing import Dict, List, Union

import numpy
import pandas
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view_types import ViewType
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View


class BoxPlotView(View):
    """
    BoxPlotView

    Base class for creating box plots.

    :property x_label: The X-axis label
    :type x_label: str
    :property y_label: The Y-axis label
    :type y_label: str
    :property x_tick_labels: The labels of X-ticks
    :type x_tick_labels: list[str]

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "max": List[Float],
                        "q1": List[Float],
                        "median": List[Float],
                        "min": List[Float],
                        "q3": List[Float],
                        "lower_whisker": List[Float],
                        "upper_whisker": List[Float],
                        "tags": List[Dict[str,str]] | None
                    },
                    "name": str
                },
                ...
            ]
        }
    }
    ```
    """

    x_label: str = None
    y_label: str = None
    x_tick_labels: List[str] = None
    _series: List = None
    _type: ViewType = ViewType.BOX_PLOT
    _title: str = "Box Plot"

    def add_data(
            self, data: Union[List[float],
                              DataFrame] = None, name: str = None, tags: List[Dict[str, str]] = None) -> None:
        """
        Add series of raw data.

        :params data: The data that will be used to compute box plots. Each data column will give one box plot.
        :type data: DataFrame or List[List[float]]
        :params tags: [optional] The list of `tags`. The length of `tags` must be equal to the number of columns in `data`
        :type tags: List[Dict[str, str]]
        """

        if data is None or not isinstance(data, list):
            raise BadRequestException("The data is required and must be an array of float")

        data = DataFrame(data)
        self.add_data_from_dataframe(DataFrame(data), name, tags)

    def add_data_from_dataframe(
            self, data: DataFrame = None, name: str = None, tags: List[Dict[str, str]] = None) -> None:
        if data is None or not isinstance(data, DataFrame):
            raise BadRequestException("The data is required and must be a DataFrame")

        if not self._series:
            self._series = []

        if tags is not None:
            if not isinstance(tags, list) or len(tags) != data.shape[1]:
                raise BadRequestException("The tags must a list of length equal to the number of columns in data")

        data = DataframeHelper.dataframe_to_float(data)

        ymin = data.min(skipna=True).to_list()
        ymax = data.max(skipna=True).to_list()

        quantile = numpy.nanquantile(data.to_numpy(), q=[0.25, 0.5, 0.75], axis=0)
        median = quantile[1, :].tolist()
        q1 = quantile[0, :]
        q3 = quantile[2, :]
        iqr = q3 - q1
        lower_whisker = q1 - (1.5 * iqr)
        upper_whisker = q3 + (1.5 * iqr)

        x = list(range(0, data.shape[1]))
        self.add_series(
            x=x,
            median=median,
            q1=q1.tolist(),
            q3=q3.tolist(),
            min=ymin,
            max=ymax,
            lower_whisker=lower_whisker.tolist(),
            upper_whisker=upper_whisker.tolist(),
            name=name,
            tags=tags
        )

    def add_series(
            self,
            x: List[float] = None,
            median: List[float] = None,
            q1: List[float] = None,
            q3: List[float] = None,
            min: List[float] = None,
            max: List[float] = None,
            lower_whisker: List[float] = None,
            upper_whisker: List[float] = None,
            name: str = None,
            tags: List[Dict[str, str]] = None) -> None:
        """
        Add series of pre-computed x and y box values.
        Vector x is the vector of bin centers and y contains the magnitudes at corresponding x positions.

        :params x: The x-axis positions of boxes
        :type x: list of float
        :params median: The median
        :type median: list of float
        :params q1: The first quartile
        :type q1: list of float
        :params q3: The third quartile
        :type q3: list of float
        :params min: The min values
        :type min: list of float
        :params max: The max values
        :type max: list of float
        :params lower_whisker: The lower_whisker values
        :type lower_whisker: list of float
        :params upper_whisker: The upper_whisker values
        :type upper_whisker: list of float
        :params tags: [optional] The list of `tags`. The length of `tags` must be equal to the number of columns in `x`
        :type tags: List[Dict[str, str]]
        """

        if not self._series:
            self._series = []

        if (median is None) or not isinstance(median, list):
            raise BadRequestException("The median data is required and must be a list of float")
        if (q1 is None) or not isinstance(q1, list):
            raise BadRequestException("The q1 data is required and must be a list of float")
        if (q3 is None) or not isinstance(q3, list):
            raise BadRequestException("The q3 data is required and must be a list of float")
        if (lower_whisker is None) or not isinstance(lower_whisker, list):
            raise BadRequestException("The lower_whisker data is required and must be a list of float")
        if (upper_whisker is None) or not isinstance(upper_whisker, list):
            raise BadRequestException("The upper_whisker data is required and must be a list of float")

        if tags is not None:
            if not isinstance(tags, list) or len(tags) != len(x):
                raise BadRequestException("The tags must a list of length equal to the length of x")
            tags = [{str(k): str(v) for k, v in t.items()} for t in tags]
        self._series.append({
            "data": {
                "x": [float(val) for val in x],
                "median": self._clean_nan(median),
                "q1": self._clean_nan(q1),
                "q3": self._clean_nan(q3),
                "min": self._clean_nan(min),
                "max": self._clean_nan(max),
                "lower_whisker": self._clean_nan(lower_whisker),
                "upper_whisker": self._clean_nan(upper_whisker),
                "tags": tags
            },
            "name": name
        })

    def to_dict(self, params: ConfigParams) -> dict:
        return {
            **super().to_dict(params),
            "data": {
                "x_label": self.x_label,
                "y_label": self.y_label,
                "x_tick_labels": self.x_tick_labels,
                "series": self._series,
            }
        }

    def _clean_nan(self, data: List[float]):
        return ['' if math.isnan(x) else float(x) for x in data]
