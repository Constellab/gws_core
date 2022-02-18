# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import FloatParam, ParamSet, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.table_meta_grouper_helper import TableMetaGrouperHelper

# ####################################################################
#
# TableDataFilter class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableMetaGrouper",
    resource_type=Table,
    short_description="Group data according to {key, value} column annotations",
)
class TableMetaGrouper(Transformer):
    config_specs: ConfigSpecs = {
        "key": StrParam(
            human_name="Key",
            short_description="Metadata key to use for data grouping",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()
        key = params["key"]
        data = TableMetaGrouperHelper.group_data(data, key)
        return Table(data=data)
