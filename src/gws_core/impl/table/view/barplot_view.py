# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import ListParam, StrParam, BoolParam
from ....resource.view_types import ViewSpecs
from ..helper.constructor.data_scale_filter_param import \
    DataScaleFilterParamConstructor
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from .base_table_view import BaseTableView
from ..helper.table_nanify_helper import TableNanifyHelper


class BarPlotView(BaseTableView):
    """
    BarPlotView

    Show a set of columns as bar plots.

    The view model is:
    ------------------

    ```
    {
        "type": "bar-plot-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                    },
                    "x_column_name": str,
                    "column_name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _type: str = "bar-plot-view"
    _data: DataFrame

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
        "use_regexp": BoolParam(default_value=False, human_name="Use regexp", short_description="True to use regular expression for column names; False otherwise"),
        "normalization": StrParam(default_value="none", allowed_values=["none", "unit", "percent"], human_name="Normalization", short_description="Type of normalization to apply on data"),
        "numeric_data_filters": NumericDataFilterParamConstructor.construct_filter(visibility='protected'),
        "text_data_filters": TextDataFilterParamConstructor.construct_filter(visibility='protected'),
        "data_scaling_filters": DataScaleFilterParamConstructor.construct_filter(visibility='protected'),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks"),
    }

    def _filter_data(self, data, params: ConfigParams):
        data = NumericDataFilterParamConstructor.validate_filter("numeric_data_filters", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_data_filters", data, params)
        data = DataScaleFilterParamConstructor.validate_filter("data_scaling_filters", data, params)
        data = TableNanifyHelper.nanify(data)
        return data

    def _normalize_data(self, data, params: ConfigParams):
        norm = params["normalization"]
        if norm and norm != "none":
            if norm == "unit":
                data = data.div(data.sum(skipna=None, axis=1), axis=0)
            elif norm == "percent":
                data = data.div(data.sum(skipna=None, axis=1), axis=0) * 100
        return data

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._data

        # apply filters
        data = self._filter_data(data, params)

        # select columns
        column_names = params.get_value("column_names", [])
        if not column_names:
            column_names = data.columns.to_list()
        else:
            if params["use_regexp"]:
                reg = "|".join([ "^"+val+"$" for val in column_names ])
                data = data.filter(regex=reg)
            else:
                column_names = [ col for col in column_names if col in data.columns]
                data = data[column_names]

        #normalization is applied at the end
        data = self._normalize_data(data, params)

        # continue ...
        x_label = params.get_value("x_label", "")
        x_tick_labels = params.get_value("x_tick_labels", data.index.to_list())
        y_label = params.get_value("y_label", "")

        # handle x tick labels
        x_tick_labels = None
        if params.value_is_set('x_tick_labels'):
            x_tick_label_columns: str = params.get_value("x_tick_labels")
            x_tick_labels = []
            for column in x_tick_label_columns:
                if column in data:
                    x_tick_labels.extend(data[column].values.tolist())

        # replace NaN by 'NaN' 
        data: DataFrame = data.fillna('')

        print(data)

        series = []
        for column_name in data.columns:
            series.append({
                "data": {
                    "x": list(range(0, data.shape[0])),
                    "y": data[column_name].values.tolist(),
                },
                "column_name": column_name,
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
