# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table

# ####################################################################
#
# TableTransposer class
#
# ####################################################################


@task_decorator(unique_name="TableTransposer", short_description="Transposes the table")
class TableTransposer(Task):
    input_specs: InputSpecs = {"table": Table}
    output_specs: OutputSpecs = {"table": Table}
    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        df: DataFrame = inputs["table"].get_data()
        return {"table": Table(data=df.T)}
