

import time
from typing import Optional

from gws_core.model.typing_style import TypingStyle

from ..config.config_params import ConfigParams
from ..config.config_types import ConfigParamsDict, ConfigSpecs
from ..config.param.param_spec import BoolParam, FloatParam, IntParam, StrParam
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..impl.shell.shell_proxy import ShellProxy
from ..io.io_spec import InputSpec, OutputSpec
from ..io.io_specs import InputSpecs, OutputSpecs
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskInputs, TaskOutputs
from .task import CheckBeforeTaskResult, Task
from .task_decorator import task_decorator


@task_decorator(unique_name="Source", human_name="Source", short_description="Select a resource from the databox",
                style=TypingStyle.material_icon("login"))
class Source(Task):
    """
    Source task.

    A source task is used to load and transfer a resource. No more action is done.
    """

    output_name: str = 'resource'
    config_name: str = 'resource_id'

    input_specs: InputSpecs = InputSpecs({})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        Resource, sub_class=True, is_constant=True, human_name="Resource", short_description="Loaded resource")})
    config_specs: ConfigSpecs = {
        'resource_id': StrParam(human_name="Resource"),
    }

    __auto_run__: bool = True

    __enable_in_sub_protocol__: bool = False

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        r_id: str = params.get_value(Source.config_name)
        if not r_id:
            raise BadRequestException(
                'Source error, the resource was not provided')

        # retrieve the resource model based and id and resource type
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(r_id)

        return {"resource": resource_model.get_resource()}

    @staticmethod
    def get_resource_id_from_config(config: ConfigParamsDict) -> Optional[str]:
        return config.get(Source.config_name, None)


@task_decorator(unique_name="Sink", human_name="Output",
                style=TypingStyle.material_icon("logout"))
class Sink(Task):
    """
    Sink task.

    A sink task is used to recieve a resource. The resource is flagged to show in databox.
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
            # mark the resource to show in databox as it is an output
            from ..resource.resource_model import ResourceModel
            resource: Resource = inputs.get(Sink.input_name)
            resource_model: ResourceModel = ResourceModel.get_by_id_and_check(
                resource.get_model_id())
            resource_model.flagged = True
            resource_model.save()

        return None


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


@task_decorator(unique_name="Wait", short_description="Wait a number of seconds specified in the config",
                style=TypingStyle.material_icon(
                    material_icon_name='front_hand',
                ),
                )
class Wait(Task):
    """
    Wait task

    This proccess waits during a given time before continuing.
    """

    input_specs: InputSpecs = InputSpecs({'resource': InputSpec(Resource)})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        resource_types=Resource, sub_class=True, is_constant=True)})
    config_specs: ConfigSpecs = {"waiting_time": FloatParam(
        default_value=3, min_value=0, short_description="The waiting time in seconds. Defaults to 3 second.")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        waiting_time = params.get_value("waiting_time")

        current_time = 0
        while (current_time < waiting_time):
            current_time = current_time + 1
            self.update_progress_value(
                (current_time / waiting_time) * 100, 'Waiting 1 sec')
            time.sleep(1)

        resource = inputs["resource"]
        return {"resource": resource}


@task_decorator(unique_name="ShellWait",
                short_description="Wait a number of seconds in the shell specified in the config",
                style=TypingStyle.material_icon(
                    material_icon_name='front_hand',
                ))
class ShellWait(Task):
    """
    Wait task

    This proccess waits during a given time before continuing.
    """

    input_specs: InputSpecs = InputSpecs({'resource': InputSpec(Resource)})
    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(
        resource_types=Resource, sub_class=True, is_constant=True)})
    config_specs: ConfigSpecs = {"waiting_time": FloatParam(
        default_value=3, min_value=0, short_description="The waiting time in seconds. Defaults to 3 second.")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Create the shell proxy. No need to provide the working directory.
        # Provide the task message_dispatcher so command outputs, will be log in the task
        shell_proxy = ShellProxy(message_dispatcher=self.message_dispatcher)

        # retrieve parameter
        waiting_time = params.get_value("waiting_time")

        # run the command
        shell_proxy.run(f"sleep {waiting_time}", shell_mode=True)

        # return the input resource as output
        resource = inputs["resource"]
        return {"resource": resource}
