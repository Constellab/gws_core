# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param.param_spec import ListParam, StrParam
from gws_core.impl.table.helper.dataframe_filter_helper import \
    DataframeFilterHelper
from gws_core.impl.table.helper.table_unfolder_helper import \
    TableUnfolderHelper
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
    """
    Transformer to unfold table rows based on provided tags.

    For each columns, the transformer will unfold the rows based on the provided tags.
    This means that the unfolder will create a new column for each tags combinaison.

    The generated column names are the concatenation of the orginial column name along with tag values.

    This task copies the orignial columns tags to the result columns.

    ## Examples
    Let's say you have the following table, the column ```row_tags``` does not really exist in the table,
    it is just to show the tags of the rows

    | row_tags                 | A | B |
    |--------------------------|---|---|
    | Gender : M <br> Age : 10 | 1 | 5 |
    | Gender : F <br> Age : 10 | 2 | 6 |
    | Gender : F <br> Age : 10 | 3 | 7 |
    | Gender : M <br> Age : 20 | 4 | 8 |

    ### Unfold with 1 tag

    Here is the result if you unfold by the tag ```Gender```

    | A_M | B_M | A_F | B_F |
    |-----|-----|-----|-----|
    | 1   | 5   | 2   | 6   |
    | 4   | 8   | 3   | 7   |

    If 1 tag key is provided, for each column it will create a new column for each tag values (here ```M``` and ```F```) and fill this column with the base original values that are tagged with the value.

    The orginial column name is changed (from ```A``` to ```'A_M``` in this example) but a new tag is add to each column containing the orignial column name. The key of the tag is configurable with the ```Tag key column name``` params (default to ```column_name```) and the value is the orinal column name. For the column ```A_M``` that new tag will be ```column_name:A```

    ### Unfold with multiple tags

    Here is the result if you unfold by the tags ```Gender``` and ```Age```

    | A_M_10 | B_M_10 | A_M_20 | B_M_20 | A_F_10 | B_F_10 |
    |--------|--------|--------|--------|--------|--------|
    | 1      | 5      | 4      | 8      | 2      | 6      |
    |        |        |        |        | 3      | 7      |

    If multiple tag keys are provided, it will create a new column for each tag values combination (here ```M-10```,  ```M-20```,  ```F-10``` and  ```F-20```) and fill this column with the original column values that are tagged with combination of tag values.

    """

    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Row tag keys",
            short_description="Row tag keys to use for data unfolding",
        ),
        "filters": DataframeFilterHelper.get_filter_param_set('column',
                                                              param_set_human_name="Column filters", optional=True),
        "tag_key_column_name": StrParam(default_value='column_name', visibility="protected", human_name='Tag key column name',
                                        short_description='Name for the column tag key that receives the column name as value'),

    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source

        if params.get('filters'):
            table = table.select_by_column_names(params.get('filters'))

        keys = params["tag_keys"]
        tag_key_column_name = params["tag_key_column_name"]
        table = TableUnfolderHelper.unfold_rows_by_tags(table, keys, tag_key_column_name)
        return table


@transformer_decorator(
    unique_name="TableColumnTagUnfold",
    human_name="Table column tag unfolder",
    resource_type=Table,
    short_description="Unfold table columns based on tags",
)
class TableColumnTagUnfolder(Transformer):
    """
    Transformer to unfold table columns based on provided tags.

    For each rows, the transformer will unfold the columns based on the provided tags.
    This means that the unfolder will create a new row for each tags combinaison.

    The generated row names are the concatenation of the orginial row name along with tag values.

    This task copies the orignial rows tags to the result rows.

    ## Examples
    See Table Row Tag Unfolder for examples.
    """
    config_specs: ConfigSpecs = {
        "tag_keys": ListParam(
            human_name="Column tag keys",
            short_description="Column tags keys to use for data unfolding",
        ),
        "filters": DataframeFilterHelper.get_filter_param_set('row',
                                                              param_set_human_name="Row filters", optional=True),

        "tag_key_row_name": StrParam(default_value='row_name', visibility="protected", human_name='Tag key rown name',
                                     short_description='Name for the row tag key that receives the row name as value'),

    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:
        table: Table = source

        if params.get('filters'):
            table = table.select_by_row_names(params.get('filters'))

        keys = params["tag_keys"]
        tag_key_row_name = params["tag_key_row_name"]
        table = TableUnfolderHelper.unfold_columns_by_tags(table, keys, tag_key_row_name)
        return table
