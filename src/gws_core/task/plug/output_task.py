
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="OutputTask", human_name="Output",
                style=TypingStyle.material_icon("logout"))
class OutputTask(Task):
    """
    Output task.

    An output task is used to recieve a resource. The resource is flagged to show resources list.
    """

    input_name: str = 'resource'
    flag_config_name: str = 'flag_resource'

    input_specs: InputSpecs = InputSpecs({'resource': InputSpec(Resource)})
    config_specs: ConfigSpecs = {
        'flag_resource': BoolParam(default_value=True, human_name="Check to flag the resource provided in the output")
    }

    __auto_run__: bool = True

    __enable_in_sub_protocol__: bool = False

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        if params.get_value('flag_resource', False):
            # mark the resource to show in list as it is an output
            from gws_core.resource.resource_model import ResourceModel
            resource: Resource = inputs.get(OutputTask.input_name)
            resource_model: ResourceModel = ResourceModel.get_by_id_and_check(
                resource.get_model_id())
            resource_model.flagged = True
            resource_model.save()

        return None
