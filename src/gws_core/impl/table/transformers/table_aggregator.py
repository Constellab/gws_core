# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.table_aggregator_helper import TableAggregatorHelper

# ####################################################################
#
# TableAggregator class
#
# ####################################################################


@transformer_decorator(unique_name="TableAggregator", resource_type=Table,
                       short_description="Aggregate the table along an axis")
class TableAggregator(Transformer):
    config_specs: ConfigSpecs = {
        "direction": StrParam(
            human_name="Direction",
            allowed_values=TableAggregatorHelper.VALID_AGGREGATION_DIRECTIONS,
            short_description="Aggregation direction",
        ),
        "function": StrParam(
            human_name="Aggregation function",
            allowed_values=TableAggregatorHelper.VALID_AXIS_AGGREGATION_FUNCTIONS,
            short_description="Function applied to aggregate value along a direction",
        ),
        "skip_nan": BoolParam(
            default_value=True,
            human_name="Skip NaN",
            short_description="Set True to skip NaN (Not-a-Number) values, False otherwise",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data = TableAggregatorHelper.aggregate(
            data=source.get_data(),
            direction=params["direction"],
            func=params["function"],
            skip_nan=params["skip_nan"]
        )
        table = Table(data=data)
        table.name = source.name + " (Aggregation)"
        return table
