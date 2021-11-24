# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams, ConfigSpecs
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from .encoded_table import EncodedTable
from .table_encoding import TableEncoding

# ####################################################################
#
# TableEncoder class
#
# ####################################################################


@task_decorator(unique_name="TableEncoder", short_description="Table encoder")
class TableEncoder(Task):
    input_specs: InputSpecs = {"table": Table, "table_encoding": TableEncoding}
    output_specs: OutputSpecs = {"encoded_table": EncodedTable}
    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        data: DataFrame = inputs["table"].get_data()
        table_encoding: TableEncoding = inputs["table_encoding"]

        ocn = table_encoding.get_original_column_name()
        ecn = table_encoding.get_encoded_column_name()
        mapper = {ocn[i]: ecn[i] for i in range(0, len(ocn))}
        data = data.rename(columns=mapper, inplace=False)

        orn = table_encoding.get_original_row_name()
        ern = table_encoding.get_encoded_row_name()
        mapper = {orn[i]: ern[i] for i in range(0, len(orn))}
        data.rename(index=mapper, inplace=True)

        encoded_table = EncodedTable(data=data, column_names=ecn, row_names=ern)
        return {"encoded_table": encoded_table}
