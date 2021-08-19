

from typing import Dict, Tuple, Type, Union

from gws_core.io.io_types import IOSpecs

from ..config.config import Config, ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io import Input, Output
from ..process.processable import Processable
from ..progress_bar.progress_bar import ProgressBar
from ..resource.resource import Resource

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

    def check_before_task(self, config: Config, inputs: Input) -> bool:
        """
        This can be overiwritten to perform custom check before running task.

        This method is systematically called before running the process task.
        If `False` is returned, the process task will not be called; otherwise, the task will proceed normally.

        :return: `True` if everything is OK, `False` otherwise. Defaults to `True`.
        :rtype: `bool`
        """

        return True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
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
