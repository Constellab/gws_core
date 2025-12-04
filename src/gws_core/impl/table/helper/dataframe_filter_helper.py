from typing import List, Literal, Union

from pandas import DataFrame, Index, api
from typing_extensions import NotRequired, TypedDict

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.config.param.tags_param_spec import TagsParam
from gws_core.core.utils.utils import Utils

from ....core.exception.exceptions import BadRequestException

AxisName = Literal["row", "column"]


class DataframeFilterName(TypedDict):
    """
    Object to filter a dataframe by name. The name can be a list of string or a string.
    If the name is a list of string, the dataframe will be filtered by the rows/columns that have one of the name.
    If the name is a string, the dataframe will be filtered by the rows/columns that have the name. The name can be a regular expression.
    """

    name: Union[List[str], str]
    is_regex: NotRequired[bool]


class DataframeFilterHelper:
    """Helper to filter dataframe rows or columns base on dataframe columns or rows"""

    @classmethod
    def _check_axis_name(cls, axis: AxisName):
        if not Utils.value_is_in_literal(axis, AxisName):
            raise BadRequestException(
                f"The axis name '{axis}' is not valid. Valid axis names are {Utils.get_literal_values(AxisName)}."
            )

    @classmethod
    def filter_by_axis_names(
        cls, data: DataFrame, axis: AxisName, filters: List[DataframeFilterName]
    ):
        dataframe: DataFrame = None
        if not isinstance(filters, list):
            raise BadRequestException("The filters must be a list of dictionnary")

        for filter_ in filters:
            new_df = cls._filter_by_axis_names(
                data, axis, filter_["name"], filter_.get("is_regex", False)
            )
            if dataframe is None:
                dataframe = new_df
            else:
                dataframe = dataframe.combine_first(new_df)

        return dataframe

    @classmethod
    def filter_out_by_axis_names(
        cls, data: DataFrame, axis: AxisName, filters: List[DataframeFilterName]
    ):
        filtered_dataframe = cls.filter_by_axis_names(data, axis, filters)

        ax_index: Index = filtered_dataframe.index if axis == "row" else filtered_dataframe.columns

        # delete the filtered rows/columns from the data
        return data.drop(labels=ax_index, axis=0 if axis == "row" else 1)

    @classmethod
    def _filter_by_axis_names(
        cls, data: DataFrame, axis: AxisName, value: Union[List[str], str], use_regexp=False
    ):
        if (not axis) or (value is None):
            return data
        cls._check_axis_name(axis)

        if not isinstance(value, list):
            value = [value]

        if not all(isinstance(x, str) for x in value) and not all(
            isinstance(x, int) for x in value
        ):
            raise BadRequestException("The names must be a list of strings or indexes")

        ax = 0 if axis == "row" else 1

        if use_regexp:
            regex = "(" + ")|(".join(value) + ")"
            return data.filter(regex=regex, axis=ax)
        else:
            ax_index: Index = data.index if axis == "row" else data.columns

            # if the index is only numeric value (default) we must convert values to int to compare
            if api.types.is_numeric_dtype(ax_index):
                value = [int(i) for i in value]

            return data.filter(items=value, axis=ax)

    @classmethod
    def get_filter_param_set(
        cls,
        axis_name: AxisName,
        param_set_human_name: str = None,
        param_set_short_description: str = None,
        optional: bool = False,
    ) -> ParamSet:
        """Get a param set that is of type DataframeFilterName"""

        human_name = "Row name" if axis_name == "row" else "Column name"
        return ParamSet(
            ConfigSpecs(
                {
                    "name": StrParam(
                        human_name=human_name,
                        short_description="Searched text or pattern (i.e. regular expression)",
                    ),
                    "is_regex": BoolParam(
                        default_value=False,
                        human_name="Use regular expression",
                        short_description="True to use regular expression, False otherwise",
                    ),
                }
            ),
            human_name=param_set_human_name,
            short_description=param_set_short_description,
            optional=optional,
        )

    @classmethod
    def get_tags_param_set(cls, axis_name: AxisName) -> ParamSet:
        """Get a param set for filtering a Table by tags"""

        human_name = "Row tags" if axis_name == "row" else "Column tags"
        return ParamSet(
            ConfigSpecs(
                {
                    "tags": TagsParam(
                        human_name=human_name,
                        short_description="If multiple tags provided, the data must have all of them (AND condition)",
                    )
                }
            ),
            human_name=human_name,
            short_description="The different tag inputs are combined with an OR condition",
        )

    @classmethod
    def convert_tags_params_to_tag_list(cls, tags: Union[dict, List[dict]]) -> List[dict]:
        """Convert a tag params from the get_tags_param_set to a list of tags"""
        if isinstance(tags, str):
            tags = [tags]

        return [tag["tags"] for tag in tags]
