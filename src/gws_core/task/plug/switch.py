
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import IntParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.task.task import CheckBeforeTaskResult, Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="Switch2", hide=True)
class Switch2(Task):
    """
    Switch task (with 2 input ports)

    The Switch2 proccess sends to the output port the resource corresponding to the parameter `index`
    """

    input_specs: InputSpecs = InputSpecs({'resource_1': InputSpec(Resource, is_optional=True),
                                          'resource_2': InputSpec(Resource, is_optional=True)})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        resource_types=Resource, sub_class=True, is_constant=True)})
    config_specs: ConfigSpecs = {"index": IntParam(
        default_value=1, min_value=1, max_value=2, short_description="The index of the input resource to switch on. Defaults to 1.")}

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        index = params.get_value("index")

        name = f"resource_{index}"
        is_ready: bool = inputs.get(name) is not None
        # The switch is ready to execute if the correct input was set
        return {"result": is_ready}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        index = params.get_value("index")
        resource = inputs[f"resource_{index}"]
        return {"resource": resource}
