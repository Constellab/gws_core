# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_aggregator_helper import (
    DfAggregationDirections, DfAggregationFunctions)
from gws_core.impl.table.helper.dataframe_data_filter_helper import \
    DataframeDataFilterHelper
from gws_core.impl.table.table import Table

from ..config.config_types import ConfigParams, ConfigSpecs
from ..config.param.param_set import ParamSet
from ..config.param.param_spec import FloatParam, StrParam
from ..task.transformer.transformer import Transformer, transformer_decorator

# ####################################################################
#
# TableAggregatorFilter class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableAggregatorFilter",
    resource_type=Table,
    short_description="Filters the table using various fitering rules", deprecated_since='0.3.14',
    deprecated_message='Use Table Column Aggregator filter or Table Row Aggregator filter instead',
    hide=True
)
class TableAggregatorFilter(Transformer):
    config_specs: ConfigSpecs = {
        "aggregation_filter": ParamSet(
            {
                "direction": StrParam(
                    human_name="Aggregation direction",
                    allowed_values=Utils.get_literal_values(DfAggregationDirections),
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
        )
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        raise Exception(
            'This transformer is deprecated. Use Table Column Aggregator filter or Table Row Aggregator filter instead')
