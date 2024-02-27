# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import pandas as pd

from gws_core.config.param.param_spec import BoolParam, ListParam, StrParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs

from ....config.config_params import ConfigParams
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..table import Table


@task_decorator("Melt", human_name="Melt",
                short_description="pandas.melt, Unpivot a DataFrame from wide to long format, optionally leaving identifiers set.",
                icon="table_chart")
class Melt(Task):
    """
    Melt from pandas \n
    input : Table \n
    output : Table \n
    Unpivot a DataFrame from wide to long format, optionally leaving identifiers set.

    This function is useful to massage a DataFrame into a format where one or
    more columns are identifier variables (id_vars), while all other columns,
    considered measured variables (value_vars), are “unpivoted” to the row
    axis, leaving just two non-identifier columns, 'variable' and 'value'.
    Do not handle multi-index columns.
    """
    input_specs = InputSpecs({'input_table': InputSpec(Table, human_name="input_table")})
    output_specs = OutputSpecs({'output_table': OutputSpec(Table, human_name="output_table")})

    config_specs = {
        "id_vars": ListParam(
            default_value=None,
            optional=True,
            human_name="id_vars",
            short_description="Column(s) to use as identifier variables."
        ),
        "value_vars": ListParam(
            default_value=None,
            human_name="value_vars",
            optional=True,
            short_description="Column(s) to unpivot. If not specified, uses all columns that are not set as *id_vars*."
        ),
        "var_name": StrParam(
            default_value=None,
            human_name="var_name",
            optional=True,
            short_description="Name to use for the 'variable' column. If None it uses `frame.columns.name` or 'variable'."
        ),
        "value_name": StrParam(
            default_value='value',
            human_name='value_name',
            optional=True,
            short_description="Name to use for the 'value' column."
        ),
        "col_level": StrParam(
            default_value=None,
            human_name="col_level",
            optional=True,
            short_description="If columns are a MultiIndex then use this level to melt."
        ),
        "ignore_index": BoolParam(
            default_value=True,
            human_name="ignore_index",
            optional=True,
            short_description="If True, original index is ignored. If False, the original index is retained. Index labels will be repeated as necessary."
        )
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        dataframe = pd.DataFrame(inputs['input_table'].get_data())
        for key, i in params.items():
            if i == "":
                params[key] = None
        result = pd.melt(dataframe,
                         id_vars=params['id_vars'],
                         value_vars=params["value_vars"],
                         var_name=params["var_name"],
                         value_name=params["value_name"],
                         col_level=params["col_level"],
                         ignore_index=params["ignore_index"])

        return {'output_table': Table(result)}
