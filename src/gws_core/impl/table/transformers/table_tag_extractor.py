# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.table.helper.table_tag_extractor_helper import \
    TableTagExtractorHelper
from gws_core.impl.table.table import Table
from gws_core.task.transformer.transformer import (Transformer,
                                                   transformer_decorator)

tag_key_param = StrParam(human_name="Tag key", short_description="Tag key to extract")

tag_type_param = StrParam(human_name="Tag values type",
                          short_description="Force tag values type, leave to char for no conversion",
                          allowed_values=TableTagExtractorHelper.TAG_EXTRACT_TYPES)


@transformer_decorator(
    unique_name="TableRowTagExtractor",
    resource_type=Table,
    short_description="Extract row tags values in a new column",
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
                                            optional=True),
                "tag_type": tag_type_param,
            },
            human_name="",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:

        result = source

        for param_dict in params["params"]:

            result = TableTagExtractorHelper.extract_row_tags(
                result, param_dict["tag_key"],
                param_dict["tag_type"],
                param_dict["new_column_name"],)

        return result


@transformer_decorator(
    unique_name="TableColumnTagExtractor",
    resource_type=Table,
    short_description="Extract column tags values in a new row",
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
                "tag_type": tag_type_param,
            },
            human_name="",
        ),
    }

    async def transform(self, source: Table, params: ConfigParams) -> Table:

        result = source

        for param_dict in params["params"]:

            result = TableTagExtractorHelper.extract_column_tags(
                result, param_dict["tag_key"],
                param_dict["tag_type"],
                param_dict["new_row_name"])

        return result
