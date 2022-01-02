# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, FloatParam, ParamSet, StrParam
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from ..helper.table_aggregator_helper import TableAggregatorHelper
from ..helper.table_filter_helper import TableFilterHelper

# ####################################################################
#
# TableFilter class
#
# ####################################################################


@task_decorator(
    unique_name="TableFilter",
    short_description="Filters the table using various fitering rules",
)
class TableFilter(Task):
    input_specs = {'source': Table}
    output_specs = {'target': Table}

    config_specs: ConfigSpecs = {
        "axis_name_filter": ParamSet(
            {
                "axis_type": StrParam(
                    default_value="column",
                    human_name="Axis type",
                    allowed_values=TableFilterHelper.VALID_AXIS_NAMES,
                    short_description="The axis whose name is searched",
                ),
                "value": StrParam(
                    human_name="Searched text",
                    short_description="Searched text or pattern (i.e. regular expression)",
                ),
                "use_regexp": BoolParam(
                    default_value=False,
                    human_name="Use regular expression",
                    short_description="True to use regular expression, False otherwise",
                )
            },
            human_name="Axis names filter",
            short_description="Filter using rows or columns name patterns",
            optional=True,
            max_number_of_occurrences=3
        ),
        "aggregation_filter": ParamSet(
            {
                "direction": StrParam(
                    human_name="Aggregation direction",
                    allowed_values=TableAggregatorHelper.VALID_AGGREGATION_DIRECTIONS,
                    short_description="Axis along which the filter is applied",
                ),
                "function": StrParam(
                    human_name="Aggregation function",
                    allowed_values=TableAggregatorHelper.VALID_AXIS_AGGREGATION_FUNCTIONS,
                    short_description="Function applied on the axis",
                ),
                "comparator": StrParam(
                    human_name="Comparator",
                    allowed_values=TableFilterHelper.VALID_NUMERIC_COMPARATORS,
                    short_description="Comparator",
                ),
                "value": FloatParam(
                    human_name="Numeric value",
                    short_description="Value",
                ),
            },
            optional=True,
            human_name="Numeric aggregation criterion",
            short_description="Filter axis validating a numeric criterion after aggregation",
            max_number_of_occurrences=3
        ),
        "numeric_data_filter": NumericDataFilterParamConstructor.construct_filter(),
        "text_data_filter": TextDataFilterParamConstructor.construct_filter(),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        data: DataFrame = inputs["source"].get_data()

        for _filter in params["axis_name_filter"]:
            data = TableFilterHelper.filter_by_axis_names(
                data=data, axis=_filter["axis_type"], value=_filter["value"], use_regexp=_filter["use_regexp"]
            )

        for _filter in params["aggregation_filter"]:
            data = TableFilterHelper.filter_by_aggregated_values(
                data=data,
                direction=_filter["direction"],
                func=_filter["function"],
                comp=_filter["comparator"],
                value=_filter["value"],
            )
        data = NumericDataFilterParamConstructor.validate_filter("numeric_data_filter", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_data_filter", data, params)

        return {'target': Table(data=data)}
