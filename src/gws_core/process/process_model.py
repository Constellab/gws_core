# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import traceback
import zlib
from enum import Enum
from typing import Dict, Type

from ..config.config_params import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
from ..process.process_io import ProcessIO
from ..resource.resource_data import ResourceData
from ..resource.resource_model import ResourceModel
from .process import Process
from .processable_model import ProcessableModel


# Enum to define the role needed for a protocol
class ProcessAllowedUser(Enum):
    ADMIN = 0
    ALL = 1


@TypingDecorator(unique_name="Process", object_type="GWS_CORE", hide=True)
class ProcessModel(ProcessableModel):
    """
    Process class.

    :property input_specs: The specs of the input
    :type input_specs: dict
    :property output_specs: The specs of the output
    :type output_specs: dict
    :property config_specs: The specs of the config
    :type config_specs: dict
    """

    _is_plug = False

    _table_name = 'gws_process'  # is locked for all processes

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """

        super().__init__(*args, **kwargs)

        if self.processable_typing_name is not None:
            self._init_io()

    def _init_io(self):
        process_type: Type[Process] = self._get_process_type()

        # input
        for k in process_type.input_specs:
            self._input.create_port(k, process_type.input_specs[k])
        if not self.data.get("input"):
            self.data["input"] = {}

        self._init_input()

        # output
        for k in process_type.output_specs:
            self._output.create_port(k, process_type.output_specs[k])
        if not self.data.get("output"):
            self.data["output"] = {}

        self._init_output()

    # -- C --

    def create_source_zip(self):
        """
        Returns the zipped code source of the process
        """

        # /:\ Use the true object type (self.type)
        model_t: Type[ProcessModel] = TypingManager.get_type_from_name(
            self.processable_typing_name)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())

    def set_process_type(self, typing_name: str) -> None:
        self.processable_typing_name = typing_name
        self._init_io()

    # -- D --

    def _create_processable_instance(self) -> Process:
        return self ._get_process_type()()

    def _get_process_type(self) -> Type[Process]:
        return TypingManager.get_type_from_name(self.processable_typing_name)

    async def _run(self) -> None:
        """
        Run the process and save its state in the database.
        """
        # Create the process instance to run the task
        process: Process = self._create_processable_instance()

        is_ok = process.check_before_task(
            config=self.config, inputs=self.input)
        if isinstance(is_ok, bool) and not is_ok:
            return
        try:
            await self._run_before_task()
            await self._run_task(process=process)
            await self._run_after_task()
        except Exception as err:
            self.progress_bar.stop(message=str(err))
            raise err

    async def _run_task(self, process: Process) -> None:
        """
        Run the process and save its state in the database.
        """
        # Get simpler object for to run the task
        config_params: ConfigParams = self.config.params
        process_input: ProcessIO = self.input.get_process_io()
        process_output: ProcessIO

        try:
            process_output = await process.task(config=config_params, inputs=process_input, progress_bar=self.progress_bar)
        except Exception as err:
            traceback.print_exc()
            raise BadRequestException(
                f"Error during the execution of the process '{self.instance_name}' in protocol '{self.parent_protocol.instance_name}' in experiment '{self.experiment.uri}'. Error : {str(err)}")

        if process_output is not None:
            # if the output is a simple dict and not a ResourceData, create a Resource Data
            if isinstance(process_output, dict) and not isinstance(process_output, ResourceData):
                process_output = ResourceData(process_output)

            # TODO do we have to check if all the required outputs have been provided ?

            # create the ResourceModel
            for key, value in process_output.items():
                # Get the type of resource model to create for this resource
                resource_model_type: Type[ResourceModel] = value.get_resource_model_type()
                if not issubclass(resource_model_type, ResourceModel):
                    raise BadRequestException(
                        f"The method get_resource_model_type of resource {value.classname()} did not return a type that extend ResourceModel")
                # create the resource model from the resource
                resource_model: ResourceModel = resource_model_type.from_resource(value)
                # save the resource model into the output
                self.output[key] = resource_model

    async def _run_after_task(self):

        if not self._is_plug:
            res: Dict[str, ResourceModel] = self.output.get_resources()
            for resource in res.values():
                if not resource is None:
                    resource.experiment = self.experiment
                    resource.process = self
                    resource.save()
        await super()._run_after_task()

    def save_full(self) -> None:
        self.config.save()
        self.progress_bar.save()
        self.save()
