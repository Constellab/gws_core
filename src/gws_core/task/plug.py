# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import Type

from gws_core.config.param_spec import FloatParam, IntParam, StrParam

from ..config.config_types import ConfigParams, ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io_spec import InputSpecs, OutputSpecs
from ..io.io_types import SkippableIn, UnmodifiedOut
from ..model.typing_manager import TypingManager
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskInputs, TaskOutputs
from .task import Task
from .task_decorator import task_decorator


@task_decorator(unique_name="Source")
class Source(Task):
    """
    Source task.

    A source task is used to load and transfer a resource. No more action is done.
    """

    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {'resource': UnmodifiedOut(Resource, sub_class=True)}
    config_specs: ConfigSpecs = {
        'resource_uri': StrParam(optional=True, short_description="The uri of the resource"),
        'resource_typing_name': StrParam(optional=True, short_description="The type of the resource"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        r_uri: str = params.get_value("resource_uri")
        r_typing_name: str = params.get_value("resource_typing_name")
        if not r_uri or not r_typing_name:
            raise BadRequestException('Source error, the resource uri or typing name is missing')

        # retrieve the resource type
        r_type: Type[Resource] = TypingManager.get_type_from_name(r_typing_name)

        # retrieve the resource model based and uri and resource type
        resource_model: ResourceModel = r_type.get_resource_model_type().get_by_uri_and_check(r_uri)

        return {"resource": resource_model.get_resource()}


@task_decorator(unique_name="Sink")
class Sink(Task):
    """
    Sink task.

    A sink task is used to recieve a resource. No action is done.
    """

    input_specs: InputSpecs = {'resource': Resource}
    output_specs: OutputSpecs = {}
    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass


@task_decorator(unique_name="FIFO2")
class FIFO2(Task):
    """
    FIFO2 task (with 2 input ports)

    The FIFO2 (First-In-First-Out) task sends to the output port the first resource received in an input port
    """

    input_specs: InputSpecs = {'resource_1': SkippableIn(Resource),
                               'resource_2': SkippableIn(Resource)}
    output_specs: OutputSpecs = {'resource': UnmodifiedOut(resource_types=Resource, sub_class=True)}
    config_specs: ConfigSpecs = {}

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> bool:
        res_1 = inputs.get('resource_1')
        res_2 = inputs.get('resource_2')
        is_ready = res_1 or res_2
        if not is_ready:
            return False

        return True

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        if inputs.has_resource("resource_1"):
            return {"resource": inputs["resource_1"]}

        if inputs.has_resource("resource_2"):
            return {"resource": inputs["resource_2"]}

        return None


@task_decorator(unique_name="Switch2")
class Switch2(Task):
    """
    Switch task (with 2 input ports)

    The Switch2 proccess sends to the output port the resource corresponding to the parameter `index`
    """

    input_specs: InputSpecs = {'resource_1': SkippableIn(Resource),
                               'resource_2': SkippableIn(Resource)}
    output_specs: OutputSpecs = {'resource': UnmodifiedOut(resource_types=Resource, sub_class=True)}
    config_specs: ConfigSpecs = {"index": IntParam(
        default_value=1, min_value=1, max_value=2, short_description="The index of the input resource to switch on. Defaults to 1.")}

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> bool:
        index = params.get_value("index")
        # The switch is ready to execute if the correct input was set
        return f"resource_{index}" in inputs

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        index = params.get_value("index")
        resource = inputs[f"resource_{index}"]
        return {"resource": resource}


@task_decorator(unique_name="Wait")
class Wait(Task):
    """
    Wait task

    This proccess waits during a given time before continuing.
    """

    input_specs: InputSpecs = {'resource': Resource}
    output_specs: OutputSpecs = {'resource': UnmodifiedOut(resource_types=Resource, sub_class=True)}
    config_specs: ConfigSpecs = {"waiting_time": FloatParam(
        default_value=3, min_value=0, short_description="The waiting time in seconds. Defaults to 3 second.")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        waiting_time = params.get_value("waiting_time")
        time.sleep(waiting_time)
        resource = inputs["resource"]
        return {"resource": resource}
