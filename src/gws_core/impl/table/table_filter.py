# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List
from pandas import DataFrame

from ...config.param_spec import BoolParam, IntParam, StrParam, ListParam
from ...config.config_types import ConfigParams, ConfigSpecs
from ...task.task_decorator import task_decorator
from ..table.table import Table
from ...task.task import Task
from ...io.io_spec import InputSpecs, OutputSpecs
from ...task.task_io import TaskInputs, TaskOutputs

# ####################################################################
#
# TableFilter class
#
# ####################################################################

@task_decorator(unique_name="TableFilter")
class TableFilter(Task):
    input_specs: InputSpecs = {'table': Table}
    output_specs: OutputSpecs = {'table': Table}
    config_specs: ConfigSpecs = {
        'row_names': ListParam(default_value=None, optional=True, short_description='Select row names'),
        'column_names': ListParam(default_value=None, optional=True, short_description='Select column names'),
        'row_mean_greater_than': IntParam(default_value=None, optional=True, short_description='Select rows with means greater than a given value'),
        'column_mean_less_than': IntParam(default_value=None, optional=True, short_description='Select columns with means less than a given value'),
        'row_std_greater_than': IntParam(default_value=None, optional=True, short_description='Select rows with standard deviations greater than a given value'),
        'column_std_less_than': IntParam(default_value=None, optional=True, short_description='Select columns with standard deviations less than a given value')
    }
    
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        df: DataFrame = inputs["table"].get_data()

        # row name
        row_names: List[str] = params.get_value('row_names')
        if row_names is not None:
            regexp = "|".join(row_names)
            df.filter(regex=regexp, axis=1)
        # row mean
        row_mean_greater_than: List[str] = params.get_value('row_mean_greater_than')
        if row_mean_greater_than is not None:
            row_means = df.mean(axis=0,numeric_only=True,skipna=True)
            df = df.loc[ row_means > row_mean_greater_than, : ]
        # row std
        row_std_greater_than: List[str] = params.get_value('row_std_greater_than')
        if row_std_greater_than is not None:
            row_std = df.std(axis=0,numeric_only=True,skipna=True)
            df = df.loc[ row_std > row_std_greater_than, : ]
        
        # column name
        column_names = params.get_value('column_names')
        if column_names is not None:
            regexp = "|".join(column_names)
            df.filter(regex=regexp, axis=1)
        # column mean
        column_mean_greater_than: List[str] = params.get_value('column_mean_greater_than')
        if column_mean_greater_than is not None:
            col_means = df.mean(axis=1,numeric_only=True,skipna=True)
            df = df.loc[ :, col_means > column_mean_greater_than ]
        # column std
        column_std_greater_than: List[str] = params.get_value('column_std_greater_than')
        if column_std_greater_than is not None:
            col_std = df.std(axis=1,numeric_only=True,skipna=True)
            df = df.loc[ :, col_std > column_std_greater_than ]
        