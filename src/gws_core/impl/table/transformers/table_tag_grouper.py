# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import ListParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ..helper.table_tag_grouper_helper import TableTagGrouperHelper
from ..table import Table


@transformer_decorator(
    unique_name="TableRowTagGrouper",
    resource_type=Table,
    short_description="Group data along row tag keys",
)
class TableRowTagGrouper(Transformer):
    """
    Aggregate row of a table by tag values.
    Provide a list of tag keys and a function to aggregate the rows.
    The task will group the rows by the tag values and apply the function to the aggregated rows.

    Available aggregation functions: ```sort```, ```mean```, ```median``` and ```sum```.

    ⚠️ **If the function ```mean``` or ```median``` is used, only 1 tag key is allowed.** ⚠️

    """
    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Tag keys",
            short_description="Tags keys to use for data grouping",
        ),
        "grouping_func": StrParam(
            allowed_values=["sort", "mean", "median", "sum"],
            human_name="Grouping function",
            short_description="The grouping function. Only one key is allowed for `mean` and `median`.",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source
        keys = params["tag_keys"]
        func = params["grouping_func"]
        table = TableTagGrouperHelper.group_by_row_tags(table, keys=keys, func=func)
        return table


@transformer_decorator(
    unique_name="TableColumnTagGrouper",
    resource_type=Table,
    short_description="Group data along column tag keys",
)
class TableColumnTagGrouper(Transformer):
    """
    Aggregate column of a table by tag values.
    Provide a list of tag keys and a function to aggregate the columns.
    The task will group the columns by the tag values and apply the function to the aggregated columns.

    Available aggregation functions: ```sort```, ```mean```, ```median``` and ```sum```.

    ⚠️ **If the function ```mean``` or ```median``` is used, only 1 tag key is allowed.** ⚠️
    """
    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Tag keys",
            short_description="Tags keys to use for data grouping",
        ),
        "grouping_func": StrParam(
            allowed_values=["sort", "mean", "median", "sum"],
            human_name="Grouping function",
            short_description="The grouping function. Only one key is allowed for `mean` and `median`.",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source
        keys = params["tag_keys"]
        func = params["grouping_func"]
        table = TableTagGrouperHelper.group_by_column_tags(table, keys=keys, func=func)
        return table
