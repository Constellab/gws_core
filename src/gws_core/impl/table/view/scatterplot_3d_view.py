# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam
from ....resource.view_types import ViewSpecs
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from .base_table_view import BaseTableView


class ScatterPlot3DView(BaseTableView):
    """
    ScatterPlot3DView

    Show a set of columns as 3d-scatter plots.

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
    """

    _type: str = "scatter-plot-3d-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "x_column_name": StrParam(human_name="X-column name", optional=True, short_description="The column to use as x-axis"),
        "y_column_name": StrParam(human_name="Y-column name", optional=True, short_description="The column to use as y-axis"),
        "z_column_names": ListParam(human_name="Z-column names", optional=True, short_description="List of columns to use as z-axis"),
        "numeric_data_filter": NumericDataFilterParamConstructor.construct_filter(visibility='protected'),
        "text_data_filter": TextDataFilterParamConstructor.construct_filter(visibility='protected'),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "z_label": StrParam(human_name="Z-label", optional=True, visibility='protected', short_description="The z-axis label to display"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
        "y_tick_labels": ListParam(human_name="Y-tick-labels", optional=True, visibility='protected', short_description="The labels of y-axis ticks"),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        # apply pre-filters
        data = self._data
        data = NumericDataFilterParamConstructor.validate_filter("numeric_data_filter", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_data_filter", data, params)

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

        series = []
        y_data = data[y_column_name].values.tolist()
        y_tick_labels = params.get_value("y_tick_labels")
        for z_column_name in z_column_names:
            z_data = data[z_column_name].values.tolist()
            series.append({
                "data": {
                    "x": x_data,
                    "y": y_data,
                    "z": z_data,
                },
                "x_column_name": x_column_name,
                "y_column_name": y_column_name,
                "z_column_name": z_column_name,
            })

        if not series:
            x_tick_labels = None
            y_tick_labels = None

        return {
            **super().to_dict(params),
            "data": {
                "x_label": x_label,
                "y_label": y_label,
                "z_label": z_label,
                "x_tick_labels": x_tick_labels,
                "y_tick_labels": y_tick_labels,
                "series": series,
            }

        }
