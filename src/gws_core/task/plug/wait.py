import time

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import FloatParam
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


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
        resource_types=Resource, sub_class=True, constant=True)})
    config_specs = ConfigSpecs({"waiting_time": FloatParam(
        default_value=3, min_value=0, short_description="The waiting time in seconds. Defaults to 3 second.")})

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
        resource_types=Resource, sub_class=True, constant=True)})
    config_specs = ConfigSpecs({"waiting_time": FloatParam(
        default_value=3, min_value=0, short_description="The waiting time in seconds. Defaults to 3 second.")})

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
