# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import zlib
from enum import Enum
from typing import Dict, Type

from ..resource.resource import Resource

from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
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

    def set_process_type(self, process_type: Type[Process]) -> None:
        self.processable_typing_name = process_type._typing_name
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
        await process.task(config=self.config, inputs=self.input, outputs=self.output, progress_bar=self.progress_bar)

    async def _run_after_task(self):

        if not self._is_plug:
            res: Dict[str, Resource] = self.output.get_resources()
            for k in res:
                if not res[k] is None:
                    res[k].experiment = self.experiment
                    res[k].process = self
                    res[k].save()
        await super()._run_after_task()

    def save_full(self) -> None:
        self.config.save()
        self.progress_bar.save()
        self.save()
