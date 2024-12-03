

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.task.task_model import TaskModel


@task_decorator(unique_name="InputTaskFromProcessOutput",
                human_name="Input from task output",
                short_description="Select a resource directly from a task output",
                style=TypingStyle.material_icon("login"))
class InputTaskFromProcessOutput(Task):
    """
    Input task to select a resource directly from a task output.
    It can be used set an input of a scenario connected to an output of a task from another scenario.
    The scenario containing this task can be created and configure before the first scenario is executed.
    It must be run after the first scenario is executed
    """

    output_name: str = 'resource'
    config_name: str = 'resource_id'

    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        Resource, sub_class=True, is_constant=True, human_name="Resource", short_description="Loaded resource")})

    config_specs: ConfigSpecs = {
        'process_model_id': StrParam(human_name="Process model id", short_description="The id of the process model that contains the output"),
        'process_output_port_name': StrParam(human_name="Output port name", short_description="The name of the output port of the process model"),
    }

    __enable_in_sub_protocol__: bool = False

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        process_model: ProcessModel = TaskModel.get_by_id(params['process_model_id'])

        if not process_model:
            process_model: ProtocolModel = ProtocolModel.get_by_id(params['process_model_id'])

        if not process_model:
            raise Exception(
                f"Process not found with id {params['process_model_id']}")

        if not process_model.is_success:
            if process_model.is_error:
                raise Exception(
                    f"Process '{process_model.name}' is in error")
            else:
                raise Exception(
                    f"Process '{process_model.name}' was not executed or is still running")

        if not process_model.outputs.port_exists(params['process_output_port_name']):
            raise Exception(
                f"Output port '{params['process_output_port_name']}' not found in the '{process_model.name}' process")

        resource = process_model.out_port(params['process_output_port_name']).get_resource()

        if not resource:
            raise Exception(
                f"Output port of the process '{process_model.name}' is empty, no resource was provided.")

        return {"resource": resource}
