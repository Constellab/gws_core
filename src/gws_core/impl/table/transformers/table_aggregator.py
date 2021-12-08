# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, StrParam
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_io import TaskInputs, TaskOutputs
from ....task.transformer.transformer_decorator import transformer_decorator
from ...table.table import Table
from ..helper.table_aggregator_helper import TableAggregatorHelper
from ..helper.table_filter_helper import TableFilterHelper

# ####################################################################
#
# TableAggregator class
#
# ####################################################################


@transformer_decorator(unique_name="TableAggregator", resource_type=Table,
                       short_description="Aggregate the table along an axis")
class TableAggregator(Task):
    input_specs: InputSpecs = {"resource": Table}
    output_specs: OutputSpecs = {"resource": Table}
    config_specs: ConfigSpecs = {
        "function": StrParam(
            human_name="Aggregation function",
            allowed_values=TableAggregatorHelper.VALID_AXIS_AGGREGATION_FUNCTIONS,
            short_description="Function applied to aggregate value along a direction",
        ),
        "direction": StrParam(
            human_name="Direction",
            allowed_values=TableAggregatorHelper.VALID_AGGREGATION_DIRECTIONS,
            short_description="Aggregation direction",
        ),
        "skip_nan": BoolParam(
            default_value=True,
            human_name="Skip NaN",
            short_description="Set True to skip NaN (Not-a-Number) values, False otherwise",
        ),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        data = TableAggregatorHelper.aggregate(
            data=inputs["resource"].get_data(),
            direction=params["direction"],
            func=params["function"],
            skip_nan=params["skip_nan"]
        )
        return {"resource": Table(data=data)}
