# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core.io.io_spec import InputSpec, OutputSpec

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigSpecs
from ....io.io_specs import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from .encoding_table import EncodingTable


@task_decorator(unique_name="TableDecoder", short_description="Table decoder",
                icon="table_chart")
class TableDecoder(Task):
    input_specs: InputSpecs = InputSpecs(
        {"encoded_table": InputSpec(Table),
         "encoding_table": InputSpec(EncodingTable)})
    output_specs: OutputSpecs = OutputSpecs({"decoded_table": OutputSpec(Table)})
    config_specs: ConfigSpecs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        encoded_data: DataFrame = inputs["encoded_table"].get_data()
        encoding_table: EncodingTable = inputs["encoding_table"]

        ocn = encoding_table.get_original_column_data()
        ecn = encoding_table.get_encoded_column_data()
        mapper = {ecn[i]: ocn[i] for i in range(0, len(ocn))}
        data = encoded_data.rename(columns=mapper, inplace=False)

        orn = encoding_table.get_original_row_data()
        ern = encoding_table.get_encoded_row_data()
        mapper = {ern[i]: orn[i] for i in range(0, len(orn))}
        data.rename(index=mapper, inplace=True)

        decoded_table = Table(data=data)
        return {"decoded_table": decoded_table}
