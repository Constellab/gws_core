# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Literal

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from .dataframe_aggregator_helper import (DataframeAggregatorHelper,
                                          DfAggregationFunctions)

DfNumericComparator = Literal["=", "!=", ">=", "<=", ">", "<"]
DfTextComparator = Literal["=", "!=", "contains", "contains not" "startswith", "endswith"]


class DataframeDataFilterHelper:
    """Helper to filter dataframe rows or columns base on dataframe values"""

    NUMERIC_COMPARATORS = Utils.get_literal_values(DfNumericComparator)
    TEXT_COMPARATORS = Utils.get_literal_values(DfTextComparator)

    @classmethod
    def filter_columns_by_aggregated_values(cls, data: DataFrame, func: DfAggregationFunctions,
                                            comp: DfNumericComparator, value: float) -> DataFrame:
        """Filter the dataframe columns based on value of the provided rows with numeric comparator"""
        if not func or not comp or value is None:
            return data
        transposed = data.T

        result = cls.filter_rows_by_aggregated_values(transposed, func, comp, value)

        return result.T

    @classmethod
    def filter_rows_by_aggregated_values(cls, data: DataFrame, func: DfAggregationFunctions,
                                         comp: DfNumericComparator, value: float) -> DataFrame:
        if not func or not comp or value is None:
            return data
        DataframeAggregatorHelper._check_func(func)
        cls._check_numeric_comparator(comp)

        aggregated_data: DataFrame = DataframeAggregatorHelper.aggregate(data, "horizontal", func)

        bool_df: DataFrame
        if comp == ">":
            bool_df = aggregated_data > value
        elif comp == ">=":
            bool_df = aggregated_data >= value
        elif comp == "<":
            bool_df = aggregated_data < value
        elif comp == "<=":
            bool_df = aggregated_data <= value
        elif comp == "=":
            bool_df = aggregated_data == value
        elif comp == "!=":
            bool_df = aggregated_data != value

        return cls._select_df_rows_from_bool_df(data, bool_df)

    @classmethod
    def filter_rows_numeric(
            cls, data: DataFrame, column_name_regex: str, comp: DfNumericComparator, value: float) -> DataFrame:
        """Filter the dataframe rows based on value of the provided columns with numeric comparator"""
        if (not column_name_regex) or (not comp) or (value is None):
            return data
        cls._check_numeric_comparator(comp)

        # keep columns based on regex
        filtered_df: DataFrame = cls._filter_columns(data, column_name_regex)

        numeric_df: DataFrame = DataframeHelper.nanify_none_numeric(filtered_df)

        bool_df: DataFrame = None
        if comp == ">":
            bool_df = numeric_df > value
        elif comp == ">=":
            bool_df = numeric_df >= value
        elif comp == "<":
            bool_df = numeric_df < value
        elif comp == "<=":
            bool_df = numeric_df <= value
        elif comp == "=":
            bool_df = numeric_df == value
        elif comp == "!=":
            bool_df = numeric_df != value

        return cls._select_df_rows_from_bool_df(data, bool_df)

    @classmethod
    def filter_rows_text(cls, data: DataFrame, column_name_regex: str, comp: DfTextComparator, value: str) -> DataFrame:
        """Filter the dataframe rows based on value of the provided columns with text comparator"""
        if (not column_name_regex) or (not comp) or (value is None):
            return data
        cls._check_text_comparator(comp)
        # keep columns based on regex
        filtered_df: DataFrame = cls._filter_columns(data, column_name_regex)

        str_df = DataframeHelper.nanify_none_str(filtered_df)

        bool_df: DataFrame = None

        if comp == "=":
            bool_df = str_df == value
        elif comp == "!=":
            bool_df = str_df != value
        elif comp == "contains":
            bool_df = DataframeHelper.contains(str_df, value)
        elif comp == "contains not":
            bool_df = DataframeHelper.contains_not(str_df, value)
        elif comp == "startswith":
            bool_df = DataframeHelper.starts_with(str_df, value)
        elif comp == "endswith":
            bool_df = DataframeHelper.ends_with(str_df, value)

        return cls._select_df_rows_from_bool_df(data, bool_df)

    @classmethod
    def filter_columns_numeric(
            cls, data: DataFrame, row_name_regex: str, comp: DfNumericComparator, value: float) -> DataFrame:
        """Filter the dataframe columns based on value of the provided rows with numeric comparator"""
        if not row_name_regex or not comp or value is None:
            return data
        transposed = data.T

        result = cls.filter_rows_numeric(transposed, row_name_regex, comp, value)

        return result.T

    @classmethod
    def filter_columns_text(cls, data: DataFrame, row_name_regex: str, comp: DfTextComparator, value: str) -> DataFrame:
        """Filter the dataframe columns based on value of the provided rows with text comparator"""
        if not row_name_regex or not comp or value is None:
            return data
        transposed = data.T

        result = cls.filter_rows_text(transposed, row_name_regex, comp, value)

        return result.T

    @classmethod
    def _filter_columns(cls, data: DataFrame, column_name_regex: str) -> DataFrame:
        """Keep columns based on regex"""
        if not column_name_regex or column_name_regex == '*':
            return data
        return data.filter(regex=column_name_regex, axis=1)

    @classmethod
    def _select_df_rows_from_bool_df(cls, data: DataFrame, bool_df: DataFrame) -> DataFrame:
        """Method to select rows from data where corresponding row in bool_df is True"""

        # convert dataframe with one column of bool
        # True when all the bool_dataframe values in a row are True
        result_df = bool_df.all(axis="columns")

        # select the rows value in result_df are True
        data = data.loc[result_df, :]

        return data

    @classmethod
    def _check_numeric_comparator(cls, comp: DfNumericComparator):
        if comp not in cls.NUMERIC_COMPARATORS:
            raise BadRequestException(
                f"The numeric comparator '{comp}' is not valid. Valid numeric comparators are {cls.NUMERIC_COMPARATORS}."
            )

    @classmethod
    def _check_text_comparator(cls, comp: DfTextComparator):
        if comp not in cls.TEXT_COMPARATORS:
            raise BadRequestException(
                f"The text comparator '{comp}' is not valid. Valid text comparators are {cls.TEXT_COMPARATORS}."
            )
