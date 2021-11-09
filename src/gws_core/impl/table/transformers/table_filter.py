# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, TypedDict

import regex
from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import (BoolParam, DictParam, FloatParam, IntParam,
                                   ListParam, ParamSet, StrParam)
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from ..helper.table_aggregator_helper import TableAggregatorHelper
from ..helper.table_filter_helper import TableFilterHelper

# ####################################################################
#
# TableFilter class
#
# ####################################################################


@task_decorator(
    unique_name="TableFilter",
    short_description="Filters the table using various fitering rules",
)
class TableFilter(Task):
    pass
    # input_specs: InputSpecs = {"table": Table}
    # output_specs: OutputSpecs = {"table": Table}
    # config_specs: ConfigSpecs = {
    #     "axis_name_filter": ParamSet(
    #         {
    #             "axis_type": StrParam(
    #                 default_value="column",
    #                 human_name="Axis type",
    #                 allowed_values=TableFilterHelper.VALID_AXIS_NAMES,
    #                 short_description="The axis whose name is searched",
    #             ),
    #             "text": StrParam(
    #                 human_name="Searched text pattern",
    #                 short_description="The row or column names are matched against the pattern",
    #             ),
    #         },
    #         human_name="Axis names filter",
    #         short_description="Filter using rows or columns name patterns",
    #         max_number_of_occurences=True
    #     ),
    #     "aggregation_filter": ParamSet(
    #         {
    #             "direction": StrParam(
    #                 human_name="Aggregation direction",
    #                 allowed_values=TableAggregatorHelper.VALID_AGGREGATION_DIRECTIONS,
    #                 short_description="Axis along which the filter is applied",
    #             ),
    #             "function": StrParam(
    #                 human_name="Aggregation function",
    #                 allowed_values=TableAggregatorHelper.VALID_AXIS_AGGREGATION_FUNCTIONS,
    #                 short_description="Function applied on the axis",
    #             ),
    #             "comparator": StrParam(
    #                 human_name="Comparator",
    #                 allowed_values=TableFilterHelper.VALID_NUMERIC_COMPARATORS,
    #                 short_description="Comparator",
    #             ),
    #             "value": FloatParam(
    #                 human_name="Numeric value",
    #                 short_description="Value",
    #             ),
    #         },
    #         optional=True,
    #         human_name="Numeric aggregation criterion",
    #         short_description="Filter axis validating a numeric criterion after aggregation",
    #         max_number_of_occurences=True
    #     ),
    #     "numeric_data_filter": ParamSet(
    #         {
    #             "column_name": StrParam(
    #                 human_name="Column name (pattern)",
    #                 short_description="The name of the columns along which the filter is applied (text pattern)",
    #             ),
    #             "comparator": StrParam(
    #                 human_name="Comparator",
    #                 allowed_values=TableFilterHelper.VALID_NUMERIC_COMPARATORS,
    #                 short_description="Comparator",
    #             ),
    #             "value": FloatParam(
    #                 human_name="Numeric value",
    #                 short_description="Value",
    #             ),
    #         },
    #         optional=True,
    #         human_name="Numeric data criterion",
    #         short_description="Filter data (along an axis) validating a numeric criterion",
    #         max_number_of_occurences=True
    #     ),
    #     "text_data_filter": ParamSet(
    #         {
    #             "column_name": StrParam(
    #                 human_name="Column name (pattern)",
    #                 short_description="The name of the columns along which the filter is applied (text pattern)",
    #             ),
    #             "comparator": StrParam(
    #                 human_name="Comparator",
    #                 allowed_values=TableFilterHelper.VALID_TEXT_COMPARATORS,
    #                 short_description="Comparator",
    #             ),
    #             "text": StrParam(
    #                 human_name="Searched text (pattern)",
    #                 short_description="Searched text (pattern)",
    #             ),
    #         },
    #         optional=True,
    #         human_name="Text data criterion",
    #         short_description="Filter data (along an axis) validating a text criterion",
    #         max_number_of_occurences=True
    #     ),
    # }

    # async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    #     data: DataFrame = inputs["table"].get_data()

    #     for _filter in params["axis_name_filter"]:
    #         data = TableFilterHelper.filter_by_axis_names(
    #             data=data, axis=_filter["axis_type"], pattern=_filter["text"]
    #         )

    #     for _filter in params["aggregation_filter"]:
    #         data = TableFilterHelper.filter_by_aggregated_values(
    #             data=data,
    #             direction=_filter["direction"],
    #             func=_filter["function"],
    #             comp=_filter["comp"],
    #             value=_filter["value"],
    #         )

    #     for _filter in params["numeric_data_filter"]:
    #         data = TableFilterHelper.filter_numeric_data(
    #             data=data,
    #             column_name=_filter["column_name"],
    #             comp=_filter["comparator"],
    #             value=_filter["value"],
    #         )

    #     for _filter in params["text_data_filter"]:
    #         data = TableFilterHelper.filter_text_data(
    #             data=data,
    #             column_name=_filter["column_name"],
    #             comp=_filter["comparator"],
    #             text=_filter["text"],
    #         )

    #     return {"table": Table(data=data)}
