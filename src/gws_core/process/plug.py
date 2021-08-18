# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import Type

from gws_core.config.config import Config
from gws_core.progress_bar.progress_bar import ProgressBar
from gws_core.resource.io import Input, Output

from ..core.model.model import Model
from ..resource.resource import Resource
from .process import Process
from .process_decorator import ProcessDecorator


@ProcessDecorator("Source")
class Source(Process):
    """
    Source process.

    A source process is used to load and transfer a resource. No more action is done.
    """

    input_specs = {}
    output_specs = {'resource': (Resource, )}
    config_specs = {
        'resource_uri': {"type": str, "default": None, 'description': "The uri of the resource"},
        'resource_type': {"type": str, "default": None, 'description': "The type of the resource"},
    }

    _is_plug = True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        r_uri = config.get_param("resource_uri")
        r_type = config.get_param("resource_type")
        if not r_uri or not r_type:
            return
        model_type: Type[Model] = Model.get_model_type(r_type)
        resource = model_type.get(model_type.uri == r_uri)
        outputs["resource"] = resource


@ProcessDecorator("Sink")
class Sink(Process):
    """
    Sink process.

    A sink process is used to recieve a resource. No action is done.
    """

    input_specs = {'resource': (Resource, )}
    output_specs = {}
    config_specs = {}
    _is_plug = True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        pass


@ProcessDecorator("FIFO2")
class FIFO2(Process):
    """
    FIFO2 process (with 2 input ports)

    The FIFO2 (First-In-First-Out) process sends to the output port the first resource received in an input port
    """

    input_specs = {'resource_1': (
        Resource, None, ), 'resource_2': (Resource, None, )}
    output_specs = {'resource': (Resource, )}
    config_specs = {}
    _is_plug = True

    def check_before_task(self, config: Config, inputs: Input) -> bool:
        res_1 = inputs['resource_1']
        res_2 = inputs['resource_2']
        is_ready = res_1 or res_2
        if not is_ready:
            return False

        return True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        resource = inputs["resource_1"]
        if resource:
            outputs["resource"] = resource
            return

        resource = inputs["resource_2"]
        if resource:
            outputs["resource"] = resource


@ProcessDecorator("Switch2")
class Switch2(Process):
    """
    Switch process (with 2 input ports)

    The Switch2 proccess sends to the output port the resource corresponding to the parameter `index`
    """

    input_specs = {'resource_1': (
        Resource, None, ), 'resource_2': (Resource, None, )}
    output_specs = {'resource': (Resource, )}
    config_specs = {
        "index": {"type": int, "default": 1, "min": 1, "max": 2, "Description": "The index of the input resource to switch on. Defaults to 1."}
    }
    _is_plug = True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        index = config.get_param("index")
        resource = inputs[f"resource_{index}"]
        outputs["resource"] = resource


@ProcessDecorator("Wait")
class Wait(Process):
    """
    Wait process

    This proccess waits during a given time before continuing.
    """

    input_specs = {'resource': (Resource,)}
    output_specs = {'resource': (Resource,)}
    config_specs = {
        "waiting_time": {"type": float, "default": 3, "min": 0, "Description": "The waiting time in seconds. Defaults to 3 second."}
    }
    _is_plug = True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        waiting_time = config.get_param("waiting_time")
        time.sleep(waiting_time)
        resource = inputs["resource"]
        outputs["resource"] = resource
