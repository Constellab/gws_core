from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.impl.table.table import Table
from gws_core.task.transformer.transformer import Transformer, transformer_decorator

tag_key_param = StrParam(human_name="Tag key", short_description="Tag key to extract")


@transformer_decorator(
    unique_name="TableRowTagExtractor",
    resource_type=Table,
    human_name="Extract row tags to new column",
    short_description="Extract row tags values to a new column",
)
class TableRowTagToColumnExtractor(Transformer):
    """

    Transformer to extract values of tags into in new columns that are appended to the end of the table.

    Multiple tag keys can be provided to extract multiple tags (one column is created by tag key).

    ## Example
    Let's say you have the following table, the column ```row_tags``` does not really exist in the table, it is just to show the tags of the rows.

    | Row tags   | A | B |
    |------------|---|---|
    | Gender : M | 1 | 5 |
    | Gender : F | 2 | 6 |

    Here is the result of the extraction of the ```Gender``` tag.

    | Row tags   | A | B | Gender |
    |------------|---|---|--------|
    | Gender : M | 1 | 5 | M      |
    | Gender : F | 2 | 6 | F      |

    The ```Gender``` column is created containing the values of the ```Gender``` tag.
    """

    config_specs = ConfigSpecs(
        {
            "params": ParamSet(
                ConfigSpecs(
                    {
                        "tag_key": tag_key_param,
                        "new_column_name": StrParam(
                            human_name="New column name",
                            short_description="Name of the new column that will contain the tag values. If empty, the tag key will be used",
                            optional=True,
                        ),
                    }
                ),
                human_name="",
            ),
        }
    )

    def transform(self, source: Table, params: ConfigParams) -> Table:
        for param_dict in params["params"]:
            source.extract_row_tags_to_new_column(
                param_dict["tag_key"], new_column_name=param_dict["new_column_name"]
            )

        return source


@transformer_decorator(
    unique_name="TableColumnTagExtractor",
    resource_type=Table,
    human_name="Extract column tags to new row",
    short_description="Extract column tags values to a new row",
)
class TableColumnTagToRowExtractor(Transformer):
    """
    Transformer to extract values of tags into in new rows that are appended to the end of the table.

    Multiple tag keys can be provided to extract multiple tags (one row is created by tag key).

    ## Example
    Let's say you have the following table, the first row does not really exist in the table, it is just to show the tags of the columns.

    | Row name    | A          | B          |
    | ----------- |------------|------------|
    | Column tags | Gender : M | Gender : F |
    | 0           | 1          | 5          |
    | 1           | 2          | 6          |

    Here is the result of the extraction of the ```Gender``` tag.

    | Row name    | A          | B          |
    | ----------- |------------|------------|
    | Column tags | Gender : M | Gender : F |
    | 0           | 1          | 5          |
    | 1           | 2          | 6          |
    | Gender      | M          | F          |


    A new row is created containing the values of the ```Gender``` tag.
    """

    config_specs = ConfigSpecs(
        {
            "params": ParamSet(
                ConfigSpecs(
                    {
                        "tag_key": tag_key_param,
                        "new_row_name": StrParam(
                            human_name="New row name",
                            short_description="Name of the new row that will contain the tag values. If empty, the tag key will be used",
                            optional=True,
                        ),
                    }
                ),
                human_name="",
            ),
        }
    )

    def transform(self, source: Table, params: ConfigParams) -> Table:
        for param_dict in params["params"]:
            source.extract_column_tags_to_new_row(
                param_dict["tag_key"], new_row_name=param_dict["new_row_name"]
            )

        return source


@transformer_decorator(
    unique_name="TableColumnValuesToRowTagExtractor",
    resource_type=Table,
    human_name="Extract column values to row tags",
    short_description="Extract the values of 1 or more columns to row tags",
)
class TableColumnValuesToRowTagExtractor(Transformer):
    """
    Transformer to extract values of columns into in row tags.

    Multiple columns can be provided to extract multiple tags (one tag is created by column).

    ## Example
    Let's say you have the following table, the first columns doesn't exist on the table, it is here to show the row tags.

    | Row tags | A          | B          |
    | -------- |------------|------------|
    |          | 1          | 5          |
    |          | 2          | 6          |

    Here is the result of the extraction of the ```A``` column.

    | Row tags | A          | B          |
    | -------- |------------|------------|
    | A : 1    | 1          | 5          |
    | A : 2    | 2          | 6          |

    The rows are tagged with the values of the ```A``` column.
    """

    config_specs = ConfigSpecs(
        {
            "params": ParamSet(
                ConfigSpecs(
                    {
                        "column": StrParam(
                            human_name="Column name",
                            short_description="Name of the column to extract values from",
                        ),
                        "delect_columns": BoolParam(
                            human_name="Delete column",
                            short_description="Delete the column after the extraction",
                            default_value=False,
                        ),
                    }
                ),
                human_name="",
            ),
        }
    )

    def transform(self, source: Table, params: ConfigParams) -> Table:
        for param_dict in params["params"]:
            source.extract_column_values_to_row_tags(
                param_dict["column"], delete_column=param_dict["delect_columns"]
            )

        return source


@transformer_decorator(
    unique_name="TableRowValuesToColumnTagExtractor",
    resource_type=Table,
    human_name="Extract row values to column tags",
    short_description="Extract the values of 1 or more rows to column tags",
)
class TableRowValuesToColumnTagExtractor(Transformer):
    """
    Transformer to extract values of rows into in column tags.

    Multiple rows can be provided to extract multiple tags (one tag is created by row).

    ## Example

    Let's say you have the following table, the first row doesn't exist on the table, it is here to show the column tags.

    | Row names | A          | B          |
    | --------  |------------|------------|
    | 0         | 1          | 5          |
    | 1         | 2          | 6          |

    Here is the result of the extraction of the ```0``` row (first row).

    | Row names   | A          | B          |
    | --------    |------------|------------|
    | Column tags | 0          | 1          |
    | 0           | 1          | 5          |
    | 1           | 2          | 6          |

    The columns are tagged with the values of the ```0``` row (first row).
    """

    config_specs = ConfigSpecs(
        {
            "params": ParamSet(
                ConfigSpecs(
                    {
                        "row": StrParam(
                            human_name="Row name",
                            short_description="Name of the row to extract values from",
                        ),
                        "delete_row": BoolParam(
                            human_name="Delete row",
                            short_description="Delete the row after the extraction",
                            default_value=False,
                        ),
                    }
                ),
                human_name="",
            ),
        }
    )

    def transform(self, source: Table, params: ConfigParams) -> Table:
        for param_dict in params["params"]:
            source.extract_row_values_to_column_tags(
                param_dict["row"], delete_row=param_dict["delete_row"]
            )

        return source
