# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.tags_param_spec import TagsParam

from ....config.config_types import ConfigParams, ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ..helper.dataframe_filter_helper import DataframeFilterHelper
from ..table import Table

# ####################################################################
#
# Table selector
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowsSelector",
    resource_type=Table,
    short_description="Select table row",
)
class TableRowSelector(Transformer):
    """
    Select part of a table using row names. Multiple row names can be provided.

    It also supports regexp.
    """

    config_specs: ConfigSpecs = {
        "filters": DataframeFilterHelper.get_filter_param_set('row')
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_row_names(params.get('filters'))


@transformer_decorator(
    unique_name="TableColumnsSelector",
    resource_type=Table,
    short_description="Select table columns",
)
class TableColumnSelector(Transformer):
    """
    Select part of a table using column names. Multiple column names can be provided.

    It also supports regexp.
    """

    config_specs: ConfigSpecs = {
        "filters": DataframeFilterHelper.get_filter_param_set('column')
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_column_names(params.get('filters'))

# ####################################################################
#
# Table tags selector
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowTagsSelector",
    resource_type=Table,
    short_description="Select table rows base on tag",
)
class TableRowTagsSelector(Transformer):
    """
    Select part of a table using row tags. Multiple row tags can be provided.
    """

    config_specs: ConfigSpecs = {
        "tags": TagsParam(
            human_name="Row tags",
            short_description="Filter on row tags",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_row_tags([params.get('tags')])


@transformer_decorator(
    unique_name="TableColumnTagsSelector",
    resource_type=Table,
    short_description="Select table column base on tag",
)
class TableColumnTagsSelector(Transformer):
    """
    Select part of a table using column tags. Multiple column tags can be provided.
    """

    config_specs: ConfigSpecs = {
        "tags": TagsParam(
            human_name="Column tags",
            short_description="Filter on column tags",
        )
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_column_tags([params.get('tags')])
