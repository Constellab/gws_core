# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource_model import ResourceModel

from ..config.config_params import ConfigParams
from ..process.process_io import ProcessInputs, ProcessOutputs
from ..resource.resource import Resource
from .process import Process
from .process_decorator import process_decorator


@process_decorator(unique_name="Source", is_plug=True)
class Source(Process):
    """
    Source process.

    A source process is used to load and transfer a resource. No more action is done.
    """

    input_specs = {}
    output_specs = {'resource': (Resource, )}
    config_specs = {
        'resource_uri': {"type": str, "default": None, 'description': "The uri of the resource"},
        'resource_typing_name': {"type": str, "default": None, 'description': "The type of the resource"},
    }

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        r_uri: str = config.get_param("resource_uri")
        r_typing_name: str = config.get_param("resource_typing_name")
        if not r_uri or not r_typing_name:
            raise BadRequestException('Source error, the resource uri or typing name is missing')
        resource_model: ResourceModel = TypingManager.get_object_with_typing_name_and_uri(
            typing_name=r_typing_name, uri=r_uri)
        return {"resource": resource_model.get_resource()}


@process_decorator(unique_name="Sink", is_plug=True)
class Sink(Process):
    """
    Sink process.

    A sink process is used to recieve a resource. No action is done.
    """

    input_specs = {'resource': (Resource, )}
    output_specs = {}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        pass


@process_decorator(unique_name="FIFO2", is_plug=True)
class FIFO2(Process):
    """
    FIFO2 process (with 2 input ports)

    The FIFO2 (First-In-First-Out) process sends to the output port the first resource received in an input port
    """

    input_specs = {'resource_1': (
        Resource, None, ), 'resource_2': (Resource, None, )}
    output_specs = {'resource': (Resource, )}
    config_specs = {}

    def check_before_task(self, config: ConfigParams, inputs: ProcessInputs) -> bool:
        res_1 = inputs['resource_1']
        res_2 = inputs['resource_2']
        is_ready = res_1 or res_2
        if not is_ready:
            return False

        return True

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        resource = inputs["resource_1"]
        if resource:
            return {"resource": resource}

        resource = inputs["resource_2"]
        if resource:
            return {"resource": resource}


@process_decorator(unique_name="Switch2", is_plug=True)
class Switch2(Process):
    """
    Switch process (with 2 input ports)

    The Switch2 proccess sends to the output port the resource corresponding to the parameter `index`
    """

    input_specs = {'resource_1': (
        Resource, None, ), 'resource_2': (Resource, None, )}
    output_specs = {'resource': (Resource, )}
    config_specs = {"index": {"type": int, "default": 1, "min": 1, "max": 2,
                              "Description": "The index of the input resource to switch on. Defaults to 1."}}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        index = config.get_param("index")
        resource = inputs[f"resource_{index}"]
        return {"resource": resource}


@process_decorator(unique_name="Wait", is_plug=True)
class Wait(Process):
    """
    Wait process

    This proccess waits during a given time before continuing.
    """

    input_specs = {'resource': (Resource,)}
    output_specs = {'resource': (Resource,)}
    config_specs = {"waiting_time": {"type": float, "default": 3, "min": 0,
                                     "Description": "The waiting time in seconds. Defaults to 3 second."}}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        waiting_time = config.get_param("waiting_time")
        time.sleep(waiting_time)
        resource = inputs["resource"]
        return {"resource": resource}
