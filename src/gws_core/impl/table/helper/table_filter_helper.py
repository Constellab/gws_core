# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import numpy
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from .table_aggregator_helper import TableAggregatorHelper


class TableFilterHelper:

    VALID_AXIS_NAMES = ["row", "column"]
    VALID_NUMERIC_COMPARATORS = ["=", "!=", ">=", "<=", ">", "<"]
    VALID_TEXT_COMPARATORS = ["=", "!=", "contains", "startswith", "endswith"]

    @classmethod
    def _check_axis_name(cls, axis):
        if axis not in cls.VALID_AXIS_NAMES:
            raise BadRequestException(
                f"The axis name '{axis}' is not valid. Valid axis names are {cls.VALID_AXIS_NAMES}."
            )

    @classmethod
    def _check_numeric_comparator(cls, comp):
        if comp not in cls.VALID_NUMERIC_COMPARATORS:
            raise BadRequestException(
                f"The numeric comparator '{comp}' is not valid. Valid numeric comparators are {cls.VALID_NUMERIC_COMPARATORS}."
            )

    @classmethod
    def _check_text_comparator(cls, comp):
        if comp not in cls.VALID_TEXT_COMPARATORS:
            raise BadRequestException(
                f"The text comparator '{comp}' is not valid. Valid text comparators are {cls.VALID_TEXT_COMPARATORS}."
            )

    @classmethod
    def filter_by_axis_names(cls, data: DataFrame, axis: str, value: str, use_regexp=False):
        if (not axis) or (value is None):
            return data
        cls._check_axis_name(axis)
        if isinstance(value, str):
            ax = 0 if axis == "row" else 1
            if use_regexp:
                return data.filter(regex=value, axis=ax)
            else:
                return data.filter(items=[value], axis=ax)
        else:
            raise BadRequestException("A string is required")

    @classmethod
    def filter_by_aggregated_values(
            cls, data: DataFrame, direction: str, func: str, comp: str, value: float) -> DataFrame:
        if (not direction) or (not func) or (not comp) or (value is None):
            return data
        TableAggregatorHelper._check_func(func)
        TableAggregatorHelper._check_direction(direction)
        cls._check_numeric_comparator(comp)
        if value is None:
            return data
        if isinstance(value, (int, float,)):
            aggregated_data: DataFrame = TableAggregatorHelper.aggregate(data, direction, func)
            tf: List[bool]
            if comp == ">":
                tf = aggregated_data > value
            elif comp == ">=":
                tf = aggregated_data >= value
            elif comp == "<":
                tf = aggregated_data < value
            elif comp == "<=":
                tf = aggregated_data <= value
            elif comp == "=":
                tf = aggregated_data == value
            elif comp == "!=":
                tf = aggregated_data != value

            if direction == "horizontal":
                return data.loc[tf[tf].index, :]
            else:
                return data.loc[:, tf[tf].index]
        else:
            raise BadRequestException("A float value is required")

    @classmethod
    def filter_numeric_data(
        cls, data: DataFrame, column_name: str, comp: str, value: float
    ) -> DataFrame:
        if (not column_name) or (not comp) or (value is None):
            return data

        tab: DataFrame = data.filter(regex=column_name, axis=1)

        def to_numeric(x):
            return x if isinstance(x, (float, int,)) else numpy.NaN
        tab = tab.applymap(to_numeric)

        if comp == ">":
            tab = tab > value
        elif comp == ">=":
            tab = tab >= value
        elif comp == "<":
            tab = tab < value
        elif comp == "<=":
            tab = tab <= value
        elif comp == "=":
            tab = tab == value
        elif comp == "!=":
            tab = tab != value

        tab = tab.all(axis="columns")
        data = data.loc[tab, :]

        return data

    @classmethod
    def filter_text_data(
            cls, data: DataFrame, column_name: str, comp: str, value: str) -> DataFrame:
        if (not column_name) or (not comp) or (value is None):
            return data
        cls._check_text_comparator(comp)
        tab: DataFrame = data.filter(regex=column_name, axis=1)

        def to_text(x):
            return x if isinstance(x, str) else numpy.NaN
        tab = tab.applymap(to_text)

        if comp == "=":
            tab = tab == value
        elif comp == "!=":
            tab = tab != value
        elif comp == "contains":
            tab = tab.str.contains(value, regexp=True)
        elif comp == "startswith":
            tab = tab.str.startswith(value)
        elif comp == "endswith":
            tab = tab.str.endswith(value)

        tab = tab.all(axis="columns")
        data = data.loc[tab, :]

        return data
