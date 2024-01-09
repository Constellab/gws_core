# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.table.table import Table
from gws_core.task.transformer.transformer import (Transformer,
                                                   transformer_decorator)

tag_key_param = StrParam(human_name="Tag key", short_description="Tag key to extract")


@transformer_decorator(
    unique_name="TableRowTagExtractor",
    resource_type=Table,
    human_name="Extract row tags to new column",
    short_description="Extract row tags values to a new column",
)
class TableRowTagExtractor(Transformer):
    """

    Transformer to extract values of tags into in new columns that are appended to the end of the table.

    Multiple tag keys can be provided to extract multiple tags (one column is created by tag key).

    ## Example
    Let's say you have the following table, the column ```row_tags``` does not really exist in the table, it is just to show the tags of the rows.

    | row_tags   | A | B |
    |------------|---|---|
    | Gender : M | 1 | 5 |
    | Gender : F | 2 | 6 |
    | Gender : F | 3 | 7 |
    | Gender : M | 4 | 8 |

    Here is the result of the extraction of the ```Gender``` tag.

    | row_tags   | A | B | Gender |
    |------------|---|---|--------|
    | Gender : M | 1 | 5 | M      |
    | Gender : F | 2 | 6 | F      |
    | Gender : F | 3 | 7 | F      |
    | Gender : M | 4 | 8 | M      |

    The ```Gender``` column is created containing the values of the ```Gender``` tag.

    ## Parameters

    - The ```New column name``` parameter allows you to define the names newly create columns that contains tags
    - The ```Tag values type```` parameters allows you to force the convertion of the tag values.
      - Use ```numeric``` to convert the tag values to float.
      - User ```char``` to keep the tag values as strings.
    """

    config_specs: ConfigSpecs = {
        "params": ParamSet(
            {
                "tag_key": tag_key_param,
                "new_column_name": StrParam(human_name="New column name",
                                            short_description="Name of the new column that will contain the tag values. If empty, the tag key will be used",
                                            optional=True)
            },
            human_name="",
        ),
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        for param_dict in params["params"]:
            source.extract_row_tags_to_new_column(param_dict["tag_key"], new_column_name=param_dict["new_column_name"])

        return source


@transformer_decorator(
    unique_name="TableColumnTagExtractor",
    resource_type=Table,
    human_name="Extract column tags to new row",
    short_description="Extract column tags values to a new row",
)
class TableColumnTagExtractor(Transformer):
    """
    Transformer to extract values of tags into in new rows that are appended to the end of the table.

    Multiple tag keys can be provided to extract multiple tags (one row is created by tag key).

    ## Example
    Let's say you have the following table, the first row does not really exist in the table, it is just to show the tags of the columns.

    | A          | B          |
    |------------|------------|
    | Gender : M | Gender : F |
    | 1          | 5          |
    | 2          | 6          |
    | 3          | 7          |
    | 4          | 8          |

    Here is the result of the extraction of the ```Gender``` tag.

    | A          | B          |
    |------------|------------|
    | Gender : M | Gender : F |
    | 1          | 5          |
    | 2          | 6          |
    | 3          | 7          |
    | 4          | 8          |
    | M          | F          |

    A new row is created containing the values of the ```Gender``` tag.

    ## Parameters

    - The ```New row name``` parameter allows you to define the names newly create rows that contains tags
    - The ```Tag values type```` parameters allows you to force the convertion of the tag values.
      - Use ```numeric``` to convert the tag values to float.
      - User ```char``` to keep the tag values as strings.
    """

    config_specs: ConfigSpecs = {
        "params": ParamSet(
            {
                "tag_key": tag_key_param,
                "new_row_name": StrParam(human_name="New row name",
                                         short_description="Name of the new row that will contain the tag values. If empty, the tag key will be used",
                                         optional=True),
            },
            human_name="",
        ),
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        for param_dict in params["params"]:
            source.extract_column_tags_to_new_row(param_dict["tag_key"], new_row_name=param_dict["new_row_name"])

        return source
