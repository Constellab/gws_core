# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_data_filter_helper import \
    DataframeDataFilterHelper
from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_set import ParamSet
from ....config.param_spec import FloatParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.dataframe_aggregator_helper import (ValidAggregationDirections,
                                                  ValidAggregationFunctions)

# ####################################################################
#
# TableAggregatorFilter class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableAggregatorFilter",
    resource_type=Table,
    short_description="Filters the table using various fitering rules",
)
class TableAggregatorFilter(Transformer):
    config_specs: ConfigSpecs = {
        "aggregation_filter": ParamSet(
            {
                "direction": StrParam(
                    human_name="Aggregation direction",
                    allowed_values=Utils.get_literal_values(ValidAggregationDirections),
                    short_description="Axis along which the filter is applied",
                ),
                "function": StrParam(
                    human_name="Aggregation function",
                    allowed_values=Utils.get_literal_values(ValidAggregationFunctions),
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
        )
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()

        for _filter in params["aggregation_filter"]:
            data = DataframeDataFilterHelper.filter_by_aggregated_values(
                data=data,
                direction=_filter["direction"],
                func=_filter["function"],
                comp=_filter["comparator"],
                value=_filter["value"],
            )

        table = Table(data=data)
        # table.name = source.name + " (Aggregation filter)"
        return table
