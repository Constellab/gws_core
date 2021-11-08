# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import numpy
import regex
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException


class TableAggregatorHelper:

    VALID_AGGREGATION_DIRECTIONS = ["horizontal", "vertical"]
    VALID_AXIS_AGGREGATION_FUNCTIONS = ["mean", "std", "var", "min", "max", "median", "sum"]

    @classmethod
    def _check_direction(cls, direction):
        if direction not in cls.VALID_AGGREGATION_DIRECTIONS:
            raise BadRequestException(
                f"The direction '{direction}' is not valid. Valid directions are {cls.VALID_AGGREGATION_DIRECTIONS}."
            )

    @classmethod
    def _check_func(cls, func):
        if func not in cls.VALID_AXIS_AGGREGATION_FUNCTIONS:
            raise BadRequestException(
                f"The aggregation function '{func}' is not valid. Valid aggregation functions are {cls.VALID_AXIS_AGGREGATION_FUNCTIONS}."
            )

    @classmethod
    def aggregate(
            cls, data: DataFrame, direction: str, func: str, skip_nan: bool = True) -> DataFrame:
        cls._check_direction(direction)
        cls._check_func(func)
        axis_num = 1 if direction == "horizontal" else 0
        aggregated_data: DataFrame
        if func == "mean":
            aggregated_data = data.mean(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )
        elif func == "std":
            aggregated_data = data.std(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )
        elif func == "var":
            aggregated_data = data.var(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )
        elif func == "max":
            aggregated_data = data.max(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )
        elif func == "min":
            aggregated_data = data.min(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )
        elif func == "median":
            aggregated_data = data.median(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )
        elif func == "sum":
            aggregated_data = data.sum(
                axis=axis_num, numeric_only=True, skipna=skip_nan
            )

        return aggregated_data
