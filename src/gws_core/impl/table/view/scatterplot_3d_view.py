# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.scatterplot_3d_view import ScatterPlot3DView
from .base_table_view import BaseTableView


class TableScatterPlot3DView(BaseTableView):
    """
    TableScatterPlot3DView

    Class for creating 3d-scatter plots using a Table.

    The view model is:
    ------------------
    ```
    {
        "type": "scatter-plot-3d-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "z_label": str,
            "x_tick_labels": List[str] | None,
            "y_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                        "z": List[Float]
                    },
                    "x_column_name": str,
                    "y_column_name": str,
                    "z_column_name": str,
                },
                ...
            ]
        }
    }
    ```

    See also ScatterPlot3DView
    """

    _type: str = "scatter-plot-3d-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "x_column_name": StrParam(human_name="X-column name", optional=True, short_description="The column to use as x-axis"),
        "y_column_name": StrParam(human_name="Y-column name", optional=True, short_description="The column to use as y-axis"),
        "z_column_names": ListParam(human_name="Z-column names", optional=True, short_description="List of columns to use as z-axis"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "z_label": StrParam(human_name="Z-label", optional=True, visibility='protected', short_description="The z-axis label to display"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
        "y_tick_labels": ListParam(human_name="Y-tick-labels", optional=True, visibility='protected', short_description="The labels of y-axis ticks"),
    }
    _view_helper: Type = ScatterPlot3DView

    def to_dict(self, params: ConfigParams) -> dict:
        if not issubclass(self._view_helper, ScatterPlot3DView):
            raise BadRequestException("Invalid view helper. An subclass of ScatterPlot2DView is expected")

        data = self._data

        # continue ...
        x_column_name = params.get_value("x_column_name", "")
        y_column_name = params.get_value("y_column_name", "")
        z_column_names = params.get_value("z_column_names", [])
        x_label = params.get_value("x_label", x_column_name)
        y_label = params.get_value("y_label", y_column_name)
        z_label = params.get_value("y_label", "")

        if x_column_name:
            x_data = data[x_column_name].values.tolist()
            x_tick_labels = None
        else:
            x_data = list(range(0, data.shape[0]))
            x_tick_labels = params.get_value("x_tick_labels", data.index.to_list())

        # replace NaN by 'NaN'
        data: DataFrame = data.fillna('')
        y_data = data[y_column_name].values.tolist()
        y_tick_labels = params.get_value("y_tick_labels")

        # create view
        view = self._view_helper()
        view.x_label = x_label
        view.y_label = y_label
        view.z_label = z_label
        view.x_tick_labels = x_tick_labels
        view.y_tick_labels = y_tick_labels
        for z_column_name in z_column_names:
            z_data = data[z_column_name].values.tolist()
            view.add_series(x_data, y_data, z_data, x_name=x_column_name, y_name=y_column_name, z_name=z_column_name)

        return view.to_dict(params)
