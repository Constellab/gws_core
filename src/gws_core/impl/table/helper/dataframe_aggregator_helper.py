from typing import Literal

from pandas import DataFrame

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper

from ....core.exception.exceptions import BadRequestException

DfAggregationDirections = Literal["horizontal", "vertical"]
DfAggregationFunctions = Literal["mean", "std", "var", "min", "max", "median", "sum"]


class DataframeAggregatorHelper:
    """Helper to aggregate dataframe rows or columns base on dataframe values"""

    AGGREGATION_DIRECTIONS = Utils.get_literal_values(DfAggregationDirections)
    AGGREGATION_FUNCTIONS = Utils.get_literal_values(DfAggregationFunctions)

    @classmethod
    def _check_direction(cls, direction: DfAggregationDirections):
        if not Utils.value_is_in_literal(direction, DfAggregationDirections):
            raise BadRequestException(
                f"The direction '{direction}' is not valid. Valid directions are {Utils.get_literal_values(DfAggregationDirections)}."
            )

    @classmethod
    def _check_func(cls, func: DfAggregationFunctions):
        if not Utils.value_is_in_literal(func, DfAggregationFunctions):
            raise BadRequestException(
                f"The aggregation function '{func}' is not valid. Valid aggregation functions are {Utils.get_literal_values(DfAggregationFunctions)}."
            )

    @classmethod
    def aggregate(
        cls,
        data: DataFrame,
        direction: DfAggregationDirections,
        func: DfAggregationFunctions,
        skip_nan: bool = True,
    ) -> DataFrame:
        if (direction is None) or (func is None):
            return data
        cls._check_direction(direction)
        cls._check_func(func)
        axis_num = 1 if direction == "horizontal" else 0

        numeric_dataframe: DataFrame = DataframeHelper.nanify_none_number(data)

        aggregated_data: DataFrame
        if func == "mean":
            aggregated_data = data.mean(axis=axis_num, numeric_only=True, skipna=skip_nan)
        elif func == "std":
            aggregated_data = data.std(axis=axis_num, numeric_only=True, skipna=skip_nan)
        elif func == "var":
            aggregated_data = data.var(axis=axis_num, numeric_only=True, skipna=skip_nan)
        elif func == "max":
            aggregated_data = data.max(axis=axis_num, numeric_only=True, skipna=skip_nan)
        elif func == "min":
            aggregated_data = data.min(axis=axis_num, numeric_only=True, skipna=skip_nan)
        elif func == "median":
            aggregated_data = data.median(axis=axis_num, numeric_only=True, skipna=skip_nan)
        elif func == "sum":
            aggregated_data = numeric_dataframe.sum(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )

        if direction == "vertical":
            aggregated_data = aggregated_data.to_frame().T
        else:
            aggregated_data = aggregated_data.to_frame()

        return aggregated_data
