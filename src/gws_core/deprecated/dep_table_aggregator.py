# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_aggregator_helper import (
    DataframeAggregatorHelper, DfAggregationDirections, DfAggregationFunctions)
from gws_core.impl.table.table import Table

from ..config.config_params import ConfigParams
from ..config.config_types import ConfigSpecs
from ..config.param.param_spec import BoolParam, StrParam
from ..task.transformer.transformer import Transformer, transformer_decorator

# ####################################################################
#
# TableAggregator class
#
# ####################################################################


@transformer_decorator(unique_name="TableAggregator", resource_type=Table,
                       short_description="Aggregate the table along an axis", deprecated_since='0.3.14',
                       deprecated_message='Use TableColumnAggregator or TableRowAggregator instead',
                       hide=True)
class TableAggregator(Transformer):
    """
    Transformer to aggregate the numerical values of table along an axis.

    Available aggregation functions: ```mean```, ```std```, ```var```, ```min```, ```max```, ```median``` and ```sum```.
    """
    config_specs: ConfigSpecs = {
        "direction": StrParam(
            human_name="Direction",
            allowed_values=Utils.get_literal_values(DfAggregationDirections),
            short_description="Aggregation direction",
        ),
        "function": StrParam(
            human_name="Aggregation function",
            allowed_values=Utils.get_literal_values(DfAggregationFunctions),
            short_description="Function applied to aggregate values along a direction",
        ),
        "skip_nan": BoolParam(
            default_value=True,
            human_name="Skip NaN",
            short_description="Set True to skip NaN (Not-a-Number) values, False otherwise",
        ),
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data = DataframeAggregatorHelper.aggregate(
            data=source.get_data(),
            direction=params["direction"],
            func=params["function"],
            skip_nan=params["skip_nan"]
        )
        table = Table(data=data)
        # table.name = source.name + " (Aggregation)"
        return table
