# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param_spec import ListParam
from gws_core.impl.table.helper.dataframe_filter_helper import \
    DataframeFilterHelper
from gws_core.impl.table.helper.table_tag_grouper_helper import \
    TableTagGrouperHelper
from gws_core.impl.table.table import Table
from gws_core.task.transformer.transformer import (Transformer,
                                                   transformer_decorator)


@transformer_decorator(
    unique_name="TableRowTagUnfold",
    human_name="Table row tag unfolder",
    resource_type=Table,
    short_description="Unfold table rows based on tags",
)
class TableRowTagUnfolder(Transformer):
    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Tag keys",
            short_description="Tags keys to use for data unfolding",
        ),
        "filters": DataframeFilterHelper.get_filter_param_set('column',
                                                              param_set_human_name="Column filters", optional=True),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source

        if params.get('filters'):
            table = table.select_by_column_names(params.get('filters'))

        keys = params["tag_keys"]
        table = TableTagGrouperHelper.unfold_rows_by_tags(table, keys=keys)
        return table


@transformer_decorator(
    unique_name="TableColumnTagUnfold",
    human_name="Table column tag unfolder",
    resource_type=Table,
    short_description="Unfold table columns based on tags",
)
class TableColumnTagUnfolder(Transformer):
    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Tag keys",
            short_description="Tags keys to use for data unfolding",
        ),
        "filters": DataframeFilterHelper.get_filter_param_set('row',
                                                              param_set_human_name="Row filters", optional=True),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source

        if params.get('filters'):
            table = table.select_by_row_names(params.get('filters'))

        keys = params["tag_keys"]
        table = TableTagGrouperHelper.unfold_columns_by_tags(table, keys=keys)
        return table
