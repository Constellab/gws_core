# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ast import Index
from typing import List, Literal, Optional, TypedDict, Union

import numpy
from gws_core.config.param_set import ParamSet
from gws_core.config.param_spec import BoolParam, StrParam
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from .dataframe_aggregator_helper import DataframeAggregatorHelper

AxisName = Literal['row', 'column']


class DataframeFilterName(TypedDict):
    name: Union[List[str], str]
    is_regex: Optional[bool]


class DataframeFilterHelper:

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
    def filter_by_axis_names(cls, data: DataFrame, axis: AxisName, value: Union[List[str], str], use_regexp=False):
        if (not axis) or (value is None):
            return data
        cls._check_axis_name(axis)

        if not isinstance(value, list):
            value = [value]

        if not all(isinstance(x, str) for x in value) and not all(isinstance(x, int) for x in value):
            raise BadRequestException("The names must be a list of strings or indexes")

        ax = 0 if axis == "row" else 1

        if use_regexp:
            regex = "(" + ")|(".join(value) + ")"
            return data.filter(regex=regex, axis=ax)
        else:
            ax_index: Index = data.index if axis == "row" else data.columns

            # if the index is only numeric value (default) we must convert values to int to compare
            if ax_index.is_numeric():
                value = [int(i) for i in value]

            return data.filter(items=value, axis=ax)

    @classmethod
    def filter_by_axis_names_2(cls, data: DataFrame, axis: AxisName, filters: List[DataframeFilterName]):
        dataframe: DataFrame = None
        for filter_ in filters:
            new_df = cls.filter_by_axis_names(data, axis, filter_["name"], filter_.get("is_regex", False))
            if dataframe is None:
                dataframe = new_df
            else:
                dataframe = dataframe.combine_first(new_df)

        return dataframe

    @classmethod
    def filter_by_aggregated_values(
            cls, data: DataFrame, direction: str, func: str, comp: str, value: float) -> DataFrame:
        if (not direction) or (not func) or (not comp) or (value is None):
            return data
        DataframeAggregatorHelper._check_func(func)
        DataframeAggregatorHelper._check_direction(direction)
        cls._check_numeric_comparator(comp)
        if value is None:
            return data
        if isinstance(value, (int, float,)):
            aggregated_data: DataFrame = DataframeAggregatorHelper.aggregate(data, direction, func)

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

            tf = tf.squeeze()  # convert to series for selection
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

    @classmethod
    def get_filter_param_set(cls, axis_name: AxisName, optional: bool = False) -> ParamSet:
        """Get a param set that is of type DataframeFilterName
        """

        human_name = "Row name" if axis_name == "row" else "Column name"
        return ParamSet({
            "name": StrParam(
                human_name=human_name,
                short_description="Searched text or pattern (i.e. regular expression)",
            ),
            "is_regex": BoolParam(
                default_value=False,
                human_name="Use regular expression",
                short_description="True to use regular expression, False otherwise",
            )
        }, optional=optional)
