# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_aggregator_helper import \
    DfAggregationFunctions
from gws_core.impl.table.helper.dataframe_data_filter_helper import \
    DataframeDataFilterHelper
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs

from ..config.config_types import ConfigParams, ConfigSpecs
from ..config.param.param_set import ParamSet
from ..config.param.param_spec import BoolParam, FloatParam, StrParam
from ..impl.table.table import Table
from ..task.task import Task
from ..task.task_decorator import task_decorator
from ..task.task_io import TaskInputs, TaskOutputs

# ####################################################################
#
# TableFilter class
#
# ####################################################################


@task_decorator(unique_name="TableFilter", human_name="Table filter",
                short_description="Filters the table using various fitering rules",
                hide=True, deprecated_since='0.2.2',
                deprecated_message='Please use TableDataFilter or TableAggregatorFilter instead')
class TableFilter(Task):
    input_specs = InputSpecs({'source': InputSpec(Table)})
    output_specs = OutputSpecs({'target': OutputSpec(Table)})

    config_specs: ConfigSpecs = {
        "axis_name_filter": ParamSet(
            {
                "axis_type": StrParam(
                    default_value="column",
                    human_name="Axis type",
                    allowed_values=["row", "column"],
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
                    allowed_values=["horizontal", "vertical"],
                    short_description="Axis along which the filter is applied",
                ),
                "function": StrParam(
                    human_name="Aggregation function",
                    allowed_values=Utils.get_literal_values(DfAggregationFunctions),
                    short_description="Function applied on the axis",
                ),
                "comparator": StrParam(
                    human_name="Comparator",
                    allowed_values=DataframeDataFilterHelper.NUMERIC_COMPARATORS,
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
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise Exception("This task is deprecated. Please use TableDataFilter or TableAggregatorFilter instead")
