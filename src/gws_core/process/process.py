

from abc import abstractmethod
from typing import Type, final

from gws_core.process.process_io import ProcessIO
from gws_core.resource.resource import Resource

from ..config.config_params import ConfigParams
from ..config.config_spec import ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io_types import IOSpecs, IOSpecsHelper
from ..processable.processable import Processable
from ..progress_bar.progress_bar import ProgressBar

# Typing names generated for the class Process
CONST_PROCESS_TYPING_NAME = "PROCESS.gws_core.Process"


class Process(Processable):

    input_specs: IOSpecs = {}
    output_specs: IOSpecs = {}
    config_specs: ConfigSpecs = {}

    def __init__(self):
        """
        Constructor
        """

        super().__init__()

        # check that the class level property _typing_name is set
        if self._typing_name is None:
            raise BadRequestException(
                f"The process {self.full_classname()} is not decorated with @ProcessDecorator, it can't be instantiate. Please decorate the process class with @ProcessDecorator")

    def check_before_task(self, config: ConfigParams, inputs: ProcessIO) -> bool:
        """
        This can be overiwritten to perform custom check before running task.

        This method is systematically called before running the process task.
        If `False` is returned, the process task will not be called; otherwise, the task will proceed normally.

        :return: `True` if everything is OK, `False` otherwise. Defaults to `True`.
        :rtype: `bool`
        """

        return True

    @abstractmethod
    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        """This must be overiwritten to perform the task of the process.

        This is where most of your code must go

        :param config: [description]
        :type config: Config
        :param inputs: [description]
        :type inputs: Input
        :param outputs: [description]
        :type outputs: Output
        :param progress_bar: [description]
        :type progress_bar: ProgressBar
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
