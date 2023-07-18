# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.impl.table.helper.dataframe_data_filter_helper import \
    DataframeDataFilterHelper
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table

# ####################################################################
#
# TableDataFilter class
#
# ####################################################################

comparator_param = StrParam(
    human_name="Comparator",
    allowed_values=DataframeDataFilterHelper.TEXT_COMPARATORS,
    short_description="Comparator",
)

value_param = StrParam(
    human_name="Text value",
    short_description="Value",
)


@transformer_decorator(
    unique_name="TableColumnDataTextFilter",
    human_name="Table column data text filter",
    resource_type=Table,
    short_description="Filters the table columns based on values of one or multiple rows with text comparator",
)
class TableColumnDataTextFilter(Transformer):
    """
    For earch filters, the system will keep the columns where the value in the row provided by the parameter ```Row name``` validated condition (the ```comparator``` with the ```value``` parameter).The result table will have the same number of rows as the input table.

    The ```Row name``` supports pattern. This means that multiple rows can be used in the filter. In this
    case all the values in the provided rows must validate the condition. You can set the value ```*``` in the ```Row name``` which mean that all the values in the column must validate the condition.

    Supported operators : ```=```, ```!=```, ```contains```, ```contains not```, ```startwith``` and ```endswith```.

If you need to apply filters on text values, you can use the ```Table column data text filter``` task.
    """
    config_specs: ConfigSpecs = {
        "text_filter": ParamSet(
            {
                "row_name_regex": StrParam(
                    human_name="Row name (pattern)",
                    short_description="The name of the rows along which the filter is applied (regexp pattern); Use '*' for all the rows",
                    optional=True,
                ),
                "comparator": comparator_param,
                "value": value_param,
            },
            visibility="public",
            human_name="Text data filters",
            max_number_of_occurrences=9
        ),
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()

        for text_params in params.get("text_filter"):
            data = DataframeDataFilterHelper.filter_columns_text(
                data=data, row_name_regex=text_params["row_name_regex"],
                comp=text_params["comparator"],
                value=text_params["value"])

        return source.create_sub_table_filtered_by_columns(data)


@transformer_decorator(
    unique_name="TableRowDataTextFilter",
    human_name="Table row data text filter",
    resource_type=Table,
    short_description="Filters the table rows based on values of one or multiple columns with text comparator",
)
class TableRowDataTextFilter(Transformer):
    """
    For earch filters, the system will keep the rows where the value in the column provided by the parameter ```Column name``` validated condition (the ```comparator``` with the ```value``` parameter).The result table will have the same number of columns as the input table.

    The ```Column name``` supports pattern. This means that multiple columns can be used in the filter. In this
    case all the values in the provided columns must validate the condition. You can set the value ```*``` in the ```Column name``` which mean that all the values in the row must validate the condition.

    Supported operators : ```=```, ```!=```, ```contains```, ```contains not```, ```startwith``` and ```endswith```.

    If you need to apply filters on text values, you can use the ```Table row data numeric filter``` task.
    """
    config_specs: ConfigSpecs = {
        "text_filter": ParamSet(
            {
                "column_name_regex": StrParam(
                    human_name="Column name (pattern)",
                    short_description="The name of the columns along which the filter is applied (regexp pattern); Use '*' for all the columns",
                    optional=True,
                ),
                "comparator": comparator_param,
                "value": value_param,
            },
            visibility="public",
            human_name="Text data filters",
            max_number_of_occurrences=9
        ),
        "stringify_table": BoolParam(default_value=False,
                                     human_name="Convert values to text",
                                     short_description="If true convert all the value (including numeric) to text. Otherwise none text value are ignored.")
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()

        if params.get("stringify_table"):
            data = DataframeHelper.stringify(data)

        for text_params in params.get("text_filter"):
            data = DataframeDataFilterHelper.filter_rows_text(
                data=data, column_name_regex=text_params["column_name_regex"],
                comp=text_params["comparator"],
                value=text_params["value"])

        return source.create_sub_table_filtered_by_rows(data)
