# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.tags_param_spec import TagsParam

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.table_filter_helper import TableFilterHelper

# ####################################################################
#
# TableColumnSelector class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableColumnsSelector",
    resource_type=Table,
    short_description="Select table columns",
)
class TableColumnSelector(Transformer):
    """
    TableColumnSelector

    Select part of a table using column name
    """

    config_specs: ConfigSpecs = {
        "column_name": StrParam(
            human_name="Column name",
            short_description="Searched text or pattern (i.e. regular expression)",
        ),
        "use_regexp": BoolParam(
            default_value=False,
            human_name="Use regular expression",
            short_description="True to use regular expression, False otherwise",
        )
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        data = TableFilterHelper.filter_by_axis_names(
            data=source.get_data(),
            axis="column",
            value=params["column_name"],
            use_regexp=params["use_regexp"]
        )

        table = Table(data=data)
        # table.name = source.name + " (Column sliced)"
        return table


@transformer_decorator(
    unique_name="TableColumnTagsSelector",
    resource_type=Table,
    short_description="Select table column base on tag",
)
class TableColumnTagsSelector(Transformer):

    config_specs: ConfigSpecs = {
        "tags": TagsParam(
            human_name="Column tags",
            short_description="Filter on column tags",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_column_tags([params.get('tags')])
