# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.io.io_spec import OutputSpec

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param.param_spec import ListParam, StrParam
from ....impl.table.table import Table
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ..dep_dataset import Dataset


@task_decorator("TableToDataset", human_name="Table to dataset converter",
                short_description="Convert a Table to dataset",
                deprecated_since='0.4.4',
                deprecated_message="Dataset is deprecated. Please use Table",
                hide=True)
class TableToDataset(Task):
    """ Convert a Table to Dataset """

    input_specs = {'table': OutputSpec(Table)}
    output_specs = {'dataset': OutputSpec(Dataset)}

    config_specs: ConfigSpecs = {
        "target_columns":
        ListParam(
            default_value=None, optional=True,
            visibility=StrParam.PUBLIC_VISIBILITY, human_name="Target columns",
            short_description="Columns to use as targets"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Convert a Table to Dataset """

        table = inputs["table"]
        target_columns = params.get("target_columns")
        dataset = Dataset.from_table(table)

        if target_columns:
            dataset.set_target_names(target_columns)

        return {"dataset": dataset}
