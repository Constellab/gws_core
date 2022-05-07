# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param_spec import BoolParam, StrParam
from gws_core.impl.table.helper.table_ratio_helper import TableRatioHelper

from ....task.transformer.transformer import Transformer, transformer_decorator
from ..table import Table


@transformer_decorator(
    unique_name="TableColumnRatio",
    resource_type=Table,
    short_description="Ration on column for a table",
)
class TableColumnRatio(Transformer):

    config_specs: ConfigSpecs = {
        "operation": StrParam(),
        "result_in_new_column":
        BoolParam(
            default_value=False, human_name="Set result in new column",
            short_description="Create a new column for the result, otherwise it only returns the result column"), }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return TableRatioHelper.columns_ratio(source, params["operation"], params["result_in_new_column"])
