

from typing import Optional

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="InputTask", human_name="Input", short_description="Select a resource",
                style=TypingStyle.material_icon("login"))
class InputTask(Task):
    """
    Standard task to load a resource into a scenario.
    This is the task used when you add a resource to a scenario.
    """

    output_name: str = 'resource'
    config_name: str = 'resource_id'

    input_specs: InputSpecs = InputSpecs({})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        Resource, sub_class=True, constant=True, human_name="Resource", short_description="Loaded resource")})
    config_specs = ConfigSpecs({
        'resource_id': StrParam(human_name="Resource"),
    }
    )
    __auto_run__: bool = True

    __enable_in_sub_protocol__: bool = False

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        r_id: str = params.get_value(InputTask.config_name)
        if not r_id:
            raise BadRequestException(
                'The resource was not provided in the configuration')

        # retrieve the resource model based and id and resource type
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(r_id)

        return {"resource": resource_model.get_resource()}

    @staticmethod
    def get_resource_id_from_config(config: ConfigParamsDict) -> Optional[str]:
        return config.get(InputTask.config_name, None)
