

from typing import Dict, List, Union

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.resource.view.view_types import ViewType

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.view.view import View


class BarPlotView(View):
    """
    BarPlotView

    Base class for creating bar plots.

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
        "type": "bar-plot-view",
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
                        "y": List[Float],
                        "tags": List[Dict[str,str]] | None
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
    x_tick_labels: List[str] = None
    x_tick_tags: List[Dict[str, str]] = None
    _series: List = None
    _type: ViewType = ViewType.BAR_PLOT
    _title: str = "Bar Plot"

    def add_series(self, x: Union[List[float], List[str], ] = None, y: List[float] = None, name: str = None,
                   tags: List[Dict[str, str]] = None):
        """
        Add a series of bars to plot

        :params x: The x-axis positions of bars
        :type x: list of float
        :params y: The y-axis magnitudes of bars
        :type y: list of float
        :params name: The name of the series
        :type name: str
        :params tags: [optional] The list of `tags`. The length of `tags` must be equal to the number of columns in `x`
        :type tags: List[Dict[str, str]]
        """

        if not self._series:
            self._series = []

        if not isinstance(y, list):
            raise BadRequestException("The y-data is required and must be a list of float")

        if x is None:
            x = self.generate_range(len(y))
        else:
            x = NumericHelper.list_to_float(x)

        y = NumericHelper.list_to_float(y)

        if tags is not None:
            if not isinstance(tags, list) or len(tags) != len(x):
                raise BadRequestException("The tags must a list of length equal to the length of x")
            tags = [{str(k): str(v) for k, v in t.items()} for t in tags]
        self._series.append({
            "data": {
                "x": x,
                "y": y,
                "tags": tags
            },
            "name": name,
        })

    def data_to_dict(self, params: ConfigParams) -> dict:
        return {
            "x_label": self.x_label,
            "y_label": self.y_label,
            "x_tick_labels": self.x_tick_labels,
            "x_tick_tags": self.x_tick_tags,
            "series": self._series,
        }
