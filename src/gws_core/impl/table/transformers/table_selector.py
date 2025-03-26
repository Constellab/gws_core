

from typing import List

from ....config.config_params import ConfigParams
from ....config.config_specs import ConfigSpecs
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
    short_description="Select table rows by name",
)
class TableRowSelector(Transformer):
    """
    Select part of a table using row names. Multiple row names can be provided.

    It also supports regexp.
    """

    config_specs = ConfigSpecs({
        "filters": DataframeFilterHelper.get_filter_param_set('row', 'Row filters')
    })

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_row_names(params.get('filters'))


@transformer_decorator(
    unique_name="TableColumnsSelector",
    resource_type=Table,
    short_description="Select table columns by name",
)
class TableColumnSelector(Transformer):
    """
    Select part of a table using column names. Multiple column names can be provided.

    It also supports regexp.
    """

    config_specs = ConfigSpecs({
        "filters": DataframeFilterHelper.get_filter_param_set('column', 'Column filters')
    })

    def transform(self, source: Table, params: ConfigParams) -> Table:
        return source.select_by_column_names(params.get('filters'))

# ####################################################################
#
# Table tags selector
#
# ####################################################################


@transformer_decorator(
    unique_name="TableRowTagsSelector",
    resource_type=Table,
    short_description="Select table rows by tags",
)
class TableRowTagsSelector(Transformer):
    """
    Select part of a table using row tags. Multiple row tags can be provided.

    # Config
    You can provide multiple tags in on input and tags in different input.

    When you provide multiple tags in one input, only the data that have **all of the tag** key/value will be selected (```AND condition```).

    When you provide tags in mulitple inputs the data that have **one of the provided tag** key/value will be selected (```OR condition```).

    You can also provide multiple tags in multiple inputs to make complexe selection.


    # Other
    If you want to delete rows by tags instead of selcting them, use the **TableRowTagsDeleter**.
    """

    config_specs = ConfigSpecs({
        'tags': DataframeFilterHelper.get_tags_param_set('row')
    })

    def transform(self, source: Table, params: ConfigParams) -> Table:
        tags: List[dict] = DataframeFilterHelper.convert_tags_params_to_tag_list(params.get('tags'))
        return source.select_by_row_tags(tags)


@transformer_decorator(
    unique_name="TableColumnTagsSelector",
    resource_type=Table,
    short_description="Select table column by tags",
)
class TableColumnTagsSelector(Transformer):
    """
    Select part of a table using column tags. Multiple column tags can be provided.

    # Config
    You can provide multiple tags in on input and tags in different input.

    When you provide multiple tags in one input, only the data that have **all of the tag** key/value will be selected (```AND condition```).

    When you provide tags in mulitple inputs the data that have **one of the provided tag** key/value will be selected (```OR condition```).

    You can also provide multiple tags in multiple inputs to make complexe selection.


    # Other
    If you want to delete columns by tags instead of selcting them, use the **TableColumnTagsDeleter**.
    """

    config_specs = ConfigSpecs({
        'tags': DataframeFilterHelper.get_tags_param_set('column')
    })

    def transform(self, source: Table, params: ConfigParams) -> Table:

        tags: List[dict] = DataframeFilterHelper.convert_tags_params_to_tag_list(params.get('tags'))
        return source.select_by_column_tags(tags)
