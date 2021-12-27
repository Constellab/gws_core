# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, StrParam
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
# TableRowSelector class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowsSelector",
    resource_type=Table,
    short_description="Select table columns",
)
class TableRowSelector(Transformer):
    config_specs: ConfigSpecs = {
        "row_name": StrParam(
            human_name="Row name",
            short_description="Searched text or pattern",
        ),
        "use_regexp": BoolParam(
            default_value=False,
            human_name="Use regular expression",
            short_description="True to use regular expression, False otherwise",
        )
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()
        data = TableFilterHelper.filter_by_axis_names(
            data=data, axis="row", value=params["row_name"], use_regexp=params["use_regexp"]
        )

        return Table(data=data)
