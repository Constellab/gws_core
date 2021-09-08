# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Type, final

from gws_core.process.process_io import ProcessInputs, ProcessOutputs
from gws_core.resource.resource import Resource

from ..config.config_params import ConfigParams
from ..config.config_spec import ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io_spec import InputSpecs, IOSpecsHelper, OutputSpecs
from ..processable.processable import Processable
from ..progress_bar.progress_bar import ProgressBar

# Typing names generated for the class Process
CONST_PROCESS_TYPING_NAME = "PROCESS.gws_core.Process"


class Process(Processable):

    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {}
    config_specs: ConfigSpecs = {}

    # Instance of the progress bar, do not use
    __progress_bar__: ProgressBar

    def __init__(self):
        """
        Constructor
        """

        super().__init__()

        # check that the class level property _typing_name is set
        if self._typing_name is None:
            raise BadRequestException(
                f"The process {self.full_classname()} is not decorated with @process_decorator, it can't be instantiate. Please decorate the process class with @process_decorator")

    def check_before_task(self, config: ConfigParams, inputs: ProcessInputs) -> bool:
        """
        This can be overiwritten to perform custom check before running task.

        This method is systematically called before running the process task.
        If `False` is returned, the process task will not be called; otherwise, the task will proceed normally.

        :return: `True` if everything is OK, `False` otherwise. Defaults to `True`.
        :rtype: `bool`
        """

        return True

    @abstractmethod
    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        """This must be overiwritten to perform the task of the process.

        This is where most of your code must go

        :param config: [description]
        :type config: Config
        :param inputs: [description]
        :type inputs: Input
        :param outputs: [description]
        :type outputs: Output
        """
        pass

    @final
    def get_default_output_spec_type(self, spec_name: str) -> Type[Resource]:
        if not self.output_specs:
            return None

        if spec_name not in self.output_specs:
            raise BadRequestException(f"The output spec does not have a spec named '{spec_name}'")

        resource_types = IOSpecsHelper.io_spec_to_resource_types(self.output_specs[spec_name])

        return resource_types[0]

    @final
    def update_progress_value(self, value: float, message: str = None):
        """Update the progress value

        :param value: value between 0 and 100 of the progress
        :type value: float
        :param message: if provided a message is stored on the progress
        :type message: str
        """
        self.__check_progres_bar__()

        self.__progress_bar__.set_value(value=value, message=message)

    @final
    def add_progress_message(self, message: str = None):
        """Store a message in the progress

        :param message: message to store in the progress
        :type message: str
        """
        self.__check_progres_bar__()

        self.__progress_bar__.add_message(message=message)

    @final
    def __check_progres_bar__(self) -> None:
        if self.__progress_bar__ is None:
            raise BadRequestException(
                "The progress bar is not defined, it can't be used inside the check_before_task method")
