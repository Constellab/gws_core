# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.task.transformer.transformer_decorator import \
    transformer_decorator
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


@transformer_decorator(unique_name="TableTransposer", resource_type=Table, short_description="Transposes the table")
class TableTransposer(Task):

    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table: Table = inputs["table"]
        data: DataFrame = table.get_data()
        transposed_table = Table(
            data=data.T,
            row_names=table.column_names,
            column_names=table.row_names
        )
        return {"table": transposed_table}
