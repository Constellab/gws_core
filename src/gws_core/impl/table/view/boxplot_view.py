# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import numpy
from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, ParamSet, StrParam, BoolParam
from ....resource.view_types import ViewSpecs
from ..helper.constructor.data_scale_filter_param import \
    DataScaleFilterParamConstructor
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from .base_table_view import BaseTableView


class BoxPlotView(BaseTableView):
    """
    BarPlotView

    Show a set of columns as box plots.

    The view model is:
    ------------------

    ```
    {
        "type": "box-plot-view",
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
                    },
                    "column_names": List[Float],
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "box-plot-view"
    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "series": ParamSet(
            {
                "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
                "use_regexp": BoolParam(default_value=False, human_name="Use regexp", short_description="True to use regular expression for column names; False otherwise"),
            },
            human_name="Column series",
            short_description="Select a series of columns to aggregate as box-plot",
            max_number_of_occurrences=5
        ),
        "numeric_data_filters": NumericDataFilterParamConstructor.construct_filter(visibility='protected'),
        "text_data_filters": TextDataFilterParamConstructor.construct_filter(visibility='protected'),
        "data_scaling_filters": DataScaleFilterParamConstructor.construct_filter(visibility='protected', allowed_values=["none", "log10", "log2"]),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
    }

    def _filter_data(self, data, params: ConfigParams):
        data = NumericDataFilterParamConstructor.validate_filter("numeric_data_filters", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_data_filters", data, params)
        data = DataScaleFilterParamConstructor.validate_filter("data_scaling_filters", data, params)
        return data

    def to_dict(self, params: ConfigParams) -> dict:
        # apply pre-filters
        data = self._data
        data = self._filter_data(data, params)

        # continue ...
        x_tick_labels = params.get_value("x_tick_labels", None)
        x_label = params.get_value("x_label", "")
        y_label = params.get_value("y_label", "")
        series = []

        for param_series in params.get("series"):
            column_names = param_series["column_names"]
            if not column_names:
                #n = min(data.shape[1], 50)
                #column_names = data.columns[0:n]
                column_names = data.columns.to_list()
            else:
                if param_series["use_regexp"]:
                    reg = "|".join([ "^"+val+"$" for val in column_names ])
                    column_names = data.filter(regex=reg).columns.to_list()
                else:
                    column_names = [ col for col in column_names if col in data.columns]

            data = data[column_names]
            
            if not len(column_names):
                continue

            if not x_tick_labels:
                x_tick_labels = column_names

            ymin = data.min(skipna=True).to_list()
            ymax = data.max(skipna=True).to_list()

            quantile = numpy.nanquantile(data.to_numpy(), q=[0.25, 0.5, 0.75], axis=0)
            median = quantile[1, :].tolist()
            q1 = quantile[0, :]
            q3 = quantile[2, :]
            iqr = q3 - q1
            lw = q1 - (1.5 * iqr)
            uw = q3 + (1.5 * iqr)

            series.append({
                "data": {
                    "median": median,
                    "q1": q1.tolist(),
                    "q3": q3.tolist(),
                    "min": ymin,
                    "max": ymax,
                    "lower_whisker": lw.tolist(),
                    "upper_whisker": uw.tolist()
                },
                "column_names": column_names,
            })

        if not series:
            x_tick_labels = None

        return {
            **super().to_dict(params),
            "data": {
                "x_label": x_label,
                "y_label": y_label,
                "x_tick_labels": x_tick_labels,
                "series": series,
            }
        }
