# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.config.param_set import ParamSet
from gws_core.config.tags_param_spec import TagsParam

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.dataframe_filter_helper import (DataframeFilterHelper,
                                              DataframeFilterName)

# ####################################################################
#
# TableRowSelector class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowsSelector",
    resource_type=Table,
    short_description="Select table row",
)
class TableRowSelector(Transformer):
    """
    TableRowSelector

    Select part of a table using row name
    """

    config_specs: ConfigSpecs = {
        "filters": DataframeFilterHelper.get_filter_param_set('row')
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_row_names(params.get('filters'))


@transformer_decorator(
    unique_name="TableRowTagsSelector",
    resource_type=Table,
    short_description="Select table rows base on tag",
)
class TableRowTagsSelector(Transformer):

    config_specs: ConfigSpecs = {
        "tags": TagsParam(
            human_name="Row tags",
            short_description="Filter on row tags",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_row_tags([params.get('tags')])
