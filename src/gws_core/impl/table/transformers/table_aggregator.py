from ....config.config_params import ConfigParams
from ....config.config_specs import ConfigSpecs
from ....config.param.param_spec import BoolParam, StrParam
from ....task.transformer.transformer import Transformer, transformer_decorator
from ...table.table import Table
from ..helper.dataframe_aggregator_helper import DataframeAggregatorHelper


@transformer_decorator(
    unique_name="TableColumnAggregator",
    resource_type=Table,
    short_description="Aggregate the table along the column axis",
)
class TableColumnAggregator(Transformer):
    """
    Transformer to aggregate the numerical values of table along the column axis.

    Available aggregation functions: ```mean```, ```std```, ```var```, ```min```, ```max```, ```median``` and ```sum```.
    """

    config_specs = ConfigSpecs(
        {
            "function": StrParam(
                human_name="Aggregation function",
                allowed_values=DataframeAggregatorHelper.AGGREGATION_FUNCTIONS,
                short_description="Function applied to aggregate values along the columns",
            ),
            "skip_nan": BoolParam(
                default_value=True,
                human_name="Skip NaN",
                short_description="If True, skip NaN values when aggregating. If False the result is NaN if one value is NaN.",
            ),
        }
    )

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data = DataframeAggregatorHelper.aggregate(
            data=source.get_data(),
            direction="vertical",
            func=params["function"],
            skip_nan=params["skip_nan"],
        )
        table = Table(data=data, column_names=source.column_names)
        table.copy_column_tags_by_index(source)
        return table


@transformer_decorator(
    unique_name="TableRowAggregator",
    resource_type=Table,
    short_description="Aggregate the table along the row axis",
)
class TableRowAggregator(Transformer):
    """
    Transformer to aggregate the numerical values of table along the row axis.

    Available aggregation functions: ```mean```, ```std```, ```var```, ```min```, ```max```, ```median``` and ```sum```.
    """

    config_specs = ConfigSpecs(
        {
            "function": StrParam(
                human_name="Aggregation function",
                allowed_values=DataframeAggregatorHelper.AGGREGATION_FUNCTIONS,
                short_description="Function applied to aggregate values along the rows",
            ),
            "skip_nan": BoolParam(
                default_value=True,
                human_name="Skip NaN",
                short_description="If True, skip NaN values when aggregating. If False the result is NaN if one value is NaN.",
            ),
        }
    )

    def transform(self, source: Table, params: ConfigParams) -> Table:
        data = DataframeAggregatorHelper.aggregate(
            data=source.get_data(),
            direction="horizontal",
            func=params["function"],
            skip_nan=params["skip_nan"],
        )
        table = Table(data=data, row_names=source.row_names)
        table.copy_row_tags_by_index(source)
        return table
