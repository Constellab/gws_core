# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import pandas as pd

from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs

from ....config.config_params import ConfigParams
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..table import Table


@task_decorator("describe", human_name='Describe', short_description="Generate short descriptive statistics")
class Describe(Task):
    """
    Descriptive statistics include those that summarize the central tendency, dispersion and shape of a dataset’s distribution, excluding `NaN` values.

    Analyzes both numeric and object series, as well as `DataFrame` column sets of mixed data types. The output will vary depending on what is provided. Refer to the notes below for more detail.

    For numeric data, the result’s index will include `count` , `mean`, `std`, min, max as well as lower, 50 and upper percentiles. By default the lower percentile is 25 and the upper percentile is 75. The 50 percentile is the same as the median.

    For object data (e.g. strings or timestamps), the result’s index will include count, unique, top, and freq. The top is the most common value. The freq is the most common value’s frequency. Timestamps also include the first and last items.

    If multiple object values have the highest count, then the count and top results will be arbitrarily chosen from among those with the highest count.

    For mixed data types provided via a DataFrame, the default is to return only an analysis of numeric columns. If the dataframe consists only of object and categorical data without any numeric columns, the default is to return an analysis of both the object and categorical columns. If include='all' is provided as an option, the result will include a union of attributes of each type.

    The include and exclude parameters can be used to limit which columns in a DataFrame are analyzed for the output. The parameters are ignored when analyzing a Series."""

    input_specs = InputSpecs({'input_table': InputSpec(Table, human_name="input_table")})
    output_specs = OutputSpecs({'output_table': OutputSpec(Table, human_name="output_table")})

    config_specs = {
        "percentiles": StrParam(
            default_value="quartiles",
            optional=True,
            human_name="percentiles",
            allowed_values=['quartiles', 'percentiles'],
            short_description="The percentiles to include in the output. should be between 0 and 1. default= [.25, .5, .75]"
        ),
        "include_NaN": BoolParam(
            default_value=False,
            human_name="include_non_numeric",
            optional=True,
            short_description="""
            Include non numeric data
            """
        ),



    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        dataframe = pd.DataFrame(inputs['input_table'].get_data())

        tiles = {'quartiles': [.25, .5, .75],
                 'percentiles': [.1, .2, .3, .4, .5, .6, .7, .8, .9, ]}
        if params["include_NaN"]:
            result = dataframe.describe(percentiles=tiles[params['percentiles']],
                                        include="all")
        else:
            result = dataframe.describe(percentiles=tiles[params['percentiles']],)

        return {"output_table": Table(result)}
