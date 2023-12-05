# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_data_filter_helper import \
    DataframeDataFilterHelper
from pandas import DataFrame

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....config.param.param_set import ParamSet
from ....config.param.param_spec import FloatParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.dataframe_aggregator_helper import DataframeAggregatorHelper


def get_function_param(axis_name: str) -> StrParam:
    return StrParam(
        human_name="Aggregation function",
        allowed_values=DataframeAggregatorHelper.AGGREGATION_FUNCTIONS,
        short_description="Function applied on the " + axis_name,
    )


comparator_param = StrParam(
    human_name="Comparator",
    allowed_values=DataframeDataFilterHelper.NUMERIC_COMPARATORS,
    short_description="Comparator",
)

value_param = FloatParam(
    human_name="Numeric value",
    short_description="Value",
)


@transformer_decorator(
    unique_name="TableColumnAggregatorFilter",
    resource_type=Table,
    short_description="Filters the table columns based aggregation value",
)
class TableColumnAggregatorFilter(Transformer):
    """
    Filter the table columns using comparator on the aggregation of the values of the columns.

    For example with this you can keep only the columns with a mean value greater than 0.5.

    The returns table is the originial table with the columns filtered (not the aggregated table).

    Supported aggregation functions: ```mean```, ```std```, ```var```, ```min```, ```max```, ```median``` and ```sum```.

    Supported comparators: ```>```, ```<```, ```>=```, ```<=```, ```==```, ```!=```.

    """
    config_specs: ConfigSpecs = {
        "aggregation_filter": ParamSet(
            {
                "function": get_function_param("columns"),
                "comparator": comparator_param,
                "value": value_param,
            },
            optional=True,
            human_name="Numeric aggregation criterion",
            short_description="Filter axis validating a numeric criterion after aggregation",
            max_number_of_occurrences=3
        )
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()

        for _filter in params["aggregation_filter"]:
            data = DataframeDataFilterHelper.filter_columns_by_aggregated_values(
                data=data,
                func=_filter["function"],
                comp=_filter["comparator"],
                value=_filter["value"],
            )

        return source.create_sub_table_filtered_by_columns(data)


@transformer_decorator(
    unique_name="TableRowAggregatorFilter",
    resource_type=Table,
    short_description="Filters the table rows based aggregation value",
)
class TableRowAggregatorFilter(Transformer):
    """
    Filter the table rows using comparator on the aggregation of the values of the rows.

    For example with this you can keep only the rows with a mean value greater than 0.5.

    The returns table is the originial table with the rows filtered (not the aggregated table).

    Supported aggregation functions: ```mean```, ```std```, ```var```, ```min```, ```max```, ```median``` and ```sum```.

    Supported comparators: ```>```, ```<```, ```>=```, ```<=```, ```==```, ```!=```.

    """
    config_specs: ConfigSpecs = {
        "aggregation_filter": ParamSet(
            {
                "function": get_function_param("rows"),
                "comparator": comparator_param,
                "value": value_param,
            },
            optional=True,
            human_name="Numeric aggregation criterion",
            short_description="Filter axis validating a numeric criterion after aggregation",
            max_number_of_occurrences=3
        )
    }

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data: DataFrame = source.get_data()

        for _filter in params["aggregation_filter"]:
            data = DataframeDataFilterHelper.filter_rows_by_aggregated_values(
                data=data,
                func=_filter["function"],
                comp=_filter["comparator"],
                value=_filter["value"],
            )

        return source.create_sub_table_filtered_by_rows(data)
