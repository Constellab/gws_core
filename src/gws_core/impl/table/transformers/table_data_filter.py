# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import FloatParam, ParamSet, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.constructor.num_data_filter_param import \
    NumericDataFilterParamConstructor
from ..helper.constructor.text_data_filter_param import \
    TextDataFilterParamConstructor
from ..helper.table_aggregator_helper import TableAggregatorHelper
from ..helper.table_filter_helper import TableFilterHelper

# ####################################################################
#
# TableDataFilter class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableDataFilter",
    resource_type=Table,
    short_description="Filters the table using various fitering rules",
)
class TableDataFilter(Transformer):
    config_specs: ConfigSpecs = {
        "numeric_filter": NumericDataFilterParamConstructor.construct_filter(),
        "text_filter": TextDataFilterParamConstructor.construct_filter(),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()
        data = NumericDataFilterParamConstructor.validate_filter("numeric_filter", data, params)
        data = TextDataFilterParamConstructor.validate_filter("text_filter", data, params)
        table = Table(data=data)
        table.name = source.name + " (Filtered)"
        return table
