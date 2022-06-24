# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import Optional

from ..config.config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from ..config.param_spec import FloatParam, IntParam, StrParam
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io_spec import InputSpec, OutputSpec
from ..io.io_spec_helper import InputSpecs, OutputSpecs
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskInputs, TaskOutputs
from .task import CheckBeforeTaskResult, Task
from .task_decorator import task_decorator


@task_decorator(unique_name="Source")
class Source(Task):
    """
    Source task.

    A source task is used to load and transfer a resource. No more action is done.
    """

    output_name: str = 'resource'
    config_name: str = 'resource_id'

    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {'resource': OutputSpec(Resource, sub_class=True, is_constant=True,
                                                        human_name="Resource", short_description="Loaded resource")}
    config_specs: ConfigSpecs = {
        'resource_id': StrParam(optional=True, short_description="The id of the resource"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        r_id: str = params.get_value(Source.config_name)
        if not r_id:
            raise BadRequestException('Source error, the resource was not provided')

        # retrieve the resource model based and id and resource type
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(r_id)

        return {"resource": resource_model.get_resource()}

    @staticmethod
    def get_resource_id_from_config(config: ConfigParamsDict) -> Optional[str]:
        return config.get(Source.config_name, None)


@task_decorator(unique_name="Sink")
class Sink(Task):
    """
    Sink task.

    A sink task is used to recieve a resource. No action is done.
    """

    input_name: str = 'resource'

    input_specs: InputSpecs = {'resource': InputSpec(Resource)}
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

    input_specs: InputSpecs = {'resource_1': InputSpec(Resource, is_skippable=True),
                               'resource_2': InputSpec(Resource, is_skippable=True)}
    output_specs: OutputSpecs = {'resource': OutputSpec(resource_types=Resource, sub_class=True, is_constant=True)}
    config_specs: ConfigSpecs = {}

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        res_1 = inputs.get('resource_1')
        res_2 = inputs.get('resource_2')
        is_ready = res_1 or res_2
        if not is_ready:
            return {"result": False}

        return {"result": True}

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

    input_specs: InputSpecs = {'resource_1': InputSpec(Resource, is_skippable=True),
                               'resource_2': InputSpec(Resource, is_skippable=True)}
    output_specs: OutputSpecs = {'resource': OutputSpec(resource_types=Resource, sub_class=True, is_constant=True)}
    config_specs: ConfigSpecs = {"index": IntParam(
        default_value=1, min_value=1, max_value=2, short_description="The index of the input resource to switch on. Defaults to 1.")}

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        index = params.get_value("index")

        is_ready: bool = f"resource_{index}" in inputs
        # The switch is ready to execute if the correct input was set
        return {"result": is_ready}

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

    input_specs: InputSpecs = {'resource': InputSpec(Resource)}
    output_specs: OutputSpecs = {'resource': OutputSpec(resource_types=Resource, sub_class=True, is_constant=True)}
    config_specs: ConfigSpecs = {"waiting_time": FloatParam(
        default_value=3, min_value=0, short_description="The waiting time in seconds. Defaults to 3 second.")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        waiting_time = params.get_value("waiting_time")

        current_time = 0
        while(current_time < waiting_time):
            self.update_progress_value((current_time / waiting_time) * 100, 'Waiting 1 sec')
            time.sleep(1)
            current_time = current_time + 1
        resource = inputs["resource"]
        return {"resource": resource}


@task_decorator(unique_name="Dispatch2")
class Dispatch2(Task):
    """
    Dispatch task (with 2 input ports)

    The Dispatch2 proccess dispatch the input data to the 2 outputs
    """

    input_specs: InputSpecs = {'resource': InputSpec(Resource)}
    output_specs: OutputSpecs = {
        'resource_1': OutputSpec(resource_types=Resource, sub_class=True, is_constant=True),
        'resource_2': OutputSpec(resource_types=Resource, sub_class=True, is_constant=True)
    }
    config_specs: ConfigSpecs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource = inputs["resource"]
        return {
            "resource_1": resource,
            "resource_2": resource
        }
