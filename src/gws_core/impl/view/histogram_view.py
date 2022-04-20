# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

import numpy
from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view_types import ViewType
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view import View


class HistogramView(View):
    """
    HistogramView

    Base class for creating histograms.

    :property x_label: The X-axis label
    :type x_label: str
    :property y_label: The Y-axis label
    :type y_label: str
    :property nbins: The number of bins
    :type nbins: int
    :property density: True to plot the density, The frequency is plotted overwise (default)
    :type density: bool
    :property x_tick_labels: The labels of X-ticks
    :type x_tick_labels: list[str]

    The view model is:
    ------------------

    ```
    {
        "type": "histogram-view",
        "title": str,
        "caption": str,
        "data": {
            "x_label": str,
            "y_label": str,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                    },
                    "name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    x_label: str = None
    y_label: str = None
    nbins: int = 10
    density: bool = False
    x_tick_labels: List[str] = None

    _series: List = None
    _type: ViewType = ViewType.HISTOGRAM
    _title: str = "Histogram"

    def add_data(self, data: List[float] = None, name: str = None):
        """
        Add series of raw data.

        :params data: The data (row or column vector) that will be used to compute histogram
        :type data: DataFrame or List[float]
        :params name: The name of the data
        :type name: str
        """

        if not self._series:
            self._series = []

        if data is None or not isinstance(data, list):
            raise BadRequestException("The data is required and must be a list of float or a DataFrame")

        data = NumericHelper.list_to_float(data, remove_none=True)

        hist, bin_edges = numpy.histogram(data, bins=self.nbins, density=self.density)
        bin_centers = (bin_edges[:-1] + bin_edges[1:])/2
        self.add_series(
            x=bin_centers.tolist(),
            y=hist.tolist(),
            name=name
        )

    def add_data_from_dataframe(self, dataframe: DataFrame = None, name: str = None) -> None:
        """
        Add series of raw data from a dataframe. The values are flattened by column
        """
        if dataframe.shape[0] != 1 and dataframe.shape[1] != 1:
            raise BadRequestException("The data must be row or column vector")
        return self.add_data(DataframeHelper.flatten_dataframe_by_column(dataframe), name=name)

    def add_series(self, *, x: Union[List[float], List[str]] = None, y: List[float] = None, name: str = None):
        """
        Add series of pre-computed x and y histogram values.
        Vector x is the vector of bin centers and y contains the magnitudes at corresponding x positions.

        :params x: The bin-center values
        :type x: list of str
        :params y: The magnitude at x positions
        :type y: list of str
        :params name: The name of the series
        :type name: str
        """

        if not self._series:
            self._series = []

        if not isinstance(x, list):
            raise BadRequestException("The x-data is required and must be a list of float")
        if not isinstance(y, list):
            raise BadRequestException("The y-data is required and must be a list of float")

        self._series.append({
            "data": {
                "x": x,
                "y": y,
            },
            "name": name,
        })

    def to_dict(self, params: ConfigParams) -> dict:
        return {
            **super().to_dict(params),
            "data": {
                "x_label": self.x_label,
                "y_label": self.y_label,
                "series": self._series,
            }
        }
