# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from .encoded_table import EncodedTable
from .encoding_table import EncodingTable

# ####################################################################
#
# TableEncoder class
#
# ####################################################################


@task_decorator(unique_name="TableEncoder", short_description="Table encoder")
class TableEncoder(Task):
    input_specs: InputSpecs = {"table": Table, "encoding_table": EncodingTable}
    output_specs: OutputSpecs = {"encoded_table": EncodedTable}
    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        data: DataFrame = inputs["table"].get_data()
        encoding_table: DataFrame = inputs["encoding_table"].get_data()

        mapper = {encoding_table.name[i]: encoding_table.code[i] for i in range(0, encoding_table.shape[0])}
        data.rename(columns=mapper, inplace=False)

        return {"table": EncodedTable(data=data)}
