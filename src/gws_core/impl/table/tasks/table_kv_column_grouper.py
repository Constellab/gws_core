# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import StrParam
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...table.table import Table
from ..encoding.annotated_table import AnnotatedTable
from ..helper.table_meta_grouper_helper import TableMetaGrouperHelper

# ####################################################################
#
# TableKVColumnGrouper class
#
# ####################################################################


@task_decorator(unique_name="TableKVColumnGrouper", short_description="Group table columns according to column keys")
class TableKVColumnGrouper(Task):
    input_specs: InputSpecs = {"table": AnnotatedTable}
    output_specs: OutputSpecs = {"table": Table}
    config_specs: ConfigSpecs = {
        "grouping_key": StrParam(
            human_name="Grouping key",
            short_description="The key used to group the columns of the table. Only for {key,value} annotated data. See also AnnotatedTable.",
        )
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        table = inputs["table"]
        data = TableMetaGrouperHelper.group_data(
            data=table.get_data(),
            key=params["grouping_key"],
            current_task=self
        )
        t = type(table)
        return {"table": t(data=data)}
