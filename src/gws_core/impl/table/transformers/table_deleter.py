# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

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
    unique_name="TableRowsDeleter",
    resource_type=Table,
    short_description="Delete table rows by name",
)
class TableRowsDeleter(Transformer):
    """
    Delete rows of a table by name. Multiple row names can be provided.

    It also supports regexp.
    """

    config_specs: ConfigSpecs = {
        "filters": DataframeFilterHelper.get_filter_param_set('row', 'Row filters')
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.filter_out_by_row_names(params.get('filters'))


@transformer_decorator(
    unique_name="TableColumnsDeleter",
    resource_type=Table,
    short_description="Delete table columns by name",
)
class TableColumnsDeleter(Transformer):
    """
    Delete columns of a table by name. Multiple column names can be provided.

    It also supports regexp.

    If you want to select column by name instead of deleting them, use the **TableColumnSelector**.
    """

    config_specs: ConfigSpecs = {
        "filters": DataframeFilterHelper.get_filter_param_set('column', 'Column filters')
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.filter_out_by_column_names(params.get('filters'))

# ####################################################################
#
# Table tags selector
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowTagsDeleter",
    resource_type=Table,
    short_description="Delete table rows by tags",
)
class TableRowTagsDeleter(Transformer):
    """
    Delete rows of the table that are tags with the provided tags. Multiple row tags can be provided.

    # Config
    You can provide multiple tags in on input and tags in different input.

    When you provide multiple tags in one input, only the data that have **all of the tag** key/value will be deleted (```AND condition```).

    When you provide tags in mulitple inputs the data that have **one of the provided tag** key/value will be deleted (```OR condition```).

    You can also provide multiple tags in multiple inputs to make complexe selection.


    # Other
    If you want to select rows by tags instead of deleting them, use the **TableRowTagsSelector**.
    """

    config_specs: ConfigSpecs = {
        'tags': DataframeFilterHelper.get_tags_param_set('row')
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        tags: List[dict] = DataframeFilterHelper.convert_tags_params_to_tag_list(params.get('tags'))
        return source.filter_out_by_tags("index", tags)


@transformer_decorator(
    unique_name="TableColumnTagsDeleter",
    resource_type=Table,
    short_description="Delete table columns by tags",
)
class TableColumnTagsDeleter(Transformer):
    """
    Delete columns of the table that are tags with the provided tags. Multiple column tags can be provided.

    # Config
    You can provide multiple tags in on input and tags in different input.

    When you provide multiple tags in one input, only the data that have **all of the tag** key/value will be deleted (```AND condition```).

    When you provide tags in mulitple inputs the data that have **one of the provided tag** key/value will be deleted (```OR condition```).

    You can also provide multiple tags in multiple inputs to make complexe selection.


    # Other
    If you want to select columns by tags instead of deleting them, use the **TableColumnTagsSelector**.
    """

    config_specs: ConfigSpecs = {
        'tags': DataframeFilterHelper.get_tags_param_set('column')
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        tags: List[dict] = DataframeFilterHelper.convert_tags_params_to_tag_list(params.get('tags'))
        return source.filter_out_by_tags("columns", tags)
