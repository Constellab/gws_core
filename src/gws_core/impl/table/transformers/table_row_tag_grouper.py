# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import ListParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.table_tag_grouper_helper import TableTagGrouperHelper

# ####################################################################
#
# TableDataFilter class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowTagGrouper",
    resource_type=Table,
    short_description="Group data along row tag keys",
)
class TableRowTagGrouper(Transformer):
    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Tag keys",
            short_description="Tags keys to use for data grouping",
        ),
        "grouping_func": StrParam(
            allowed_values=["sort", "mean", "median"],
            human_name="Grouping function",
            short_description="The grouping function. Only one key is allowed for `mean` and `median`.",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source
        keys = params["tag_keys"]
        func = params["grouping_func"]
        table = TableTagGrouperHelper.group_by_row_tags(table, keys=keys, func=func)
        # table.name = source.name + " (sliced along row tag)"
        return table
