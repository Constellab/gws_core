# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.impl.table.table import Table
from gws_core.task.transformer.transformer_decorator import \
    transformer_decorator

from ....config.config_types import ConfigParams, ConfigSpecs
from ....io.io_spec import InputSpecs, OutputSpecs
from ....task.task import Task
from ....task.task_io import TaskInputs, TaskOutputs
from ..helper.constructor.data_scale_filter_param import \
    DataScaleFilterParamConstructor

# ####################################################################
#
# TableScaler class
#
# ####################################################################


@transformer_decorator(
    unique_name="TableScaler",
    resource_type=Table,
    short_description="Scales the numeric values of the table",
)
class TableScaler(Task):
    input_specs: InputSpecs = {"resource": Table}
    output_specs: OutputSpecs = {"resource": Table}
    config_specs: ConfigSpecs = {
        "data_scaling_filter": DataScaleFilterParamConstructor.construct_filter(),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        data = inputs["resource"].get_data()
        data = DataScaleFilterParamConstructor.validate_filter("data_scaling_filters", data, params)
        return {"resource": Table(data=data)}
