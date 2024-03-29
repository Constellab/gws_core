

from typing import List, Literal, Union

import numpy
from pandas import DataFrame

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view.view import View

HistogramMode = Literal["FREQUENCY", "DENSITY", "PROBABILITY"]


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
    nbins: int = None
    mode: HistogramMode = None
    x_tick_labels: List[str] = None

    _series: List = None
    _type: ViewType = ViewType.HISTOGRAM
    _title: str = "Histogram"

    def __init__(self,
                 nbins: int = 10, mode: HistogramMode = "FREQUENCY"):
        super().__init__()
        self.nbins = nbins
        self.mode = mode

    def add_data(self, data: List[float] = None, name: str = None) -> None:
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

        nbins = self.nbins
        if nbins is None or nbins <= 0:
            nbins = 10

        data = NumericHelper.list_to_float(data, remove_none=True)

        density = self.mode == "DENSITY"

        hist, bin_edges = numpy.histogram(data, bins=nbins, density=density)

        # normalize the histogram
        if self.mode == "PROBABILITY":
            hist = hist / hist.sum()

        self.add_series(
            x=bin_edges.tolist(),
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

    def add_series(self, x: Union[List[float], List[str]] = None, y: List[float] = None, name: str = None):
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

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "x_label": self.x_label,
            "y_label": self.y_label,
            "series": self._series,
            "mode": self.mode,
        }
