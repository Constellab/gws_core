

from ..config.config import Config
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..progress_bar.progress_bar import ProgressBar
from ..resource.io import Input, Output
from .processable import Processable

# Typing names generated for the class Process
CONST_PROCESS_TYPING_NAME = "PROCESS.gws_core.Process"


class Process(Processable):

    input_specs: dict = {}
    output_specs: dict = {}
    config_specs: dict = {}

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
        This must be overloaded to perform custom check before running task.

        This method is systematically called before running the process task.
        If `False` is returned, the process task will not be called; otherwise, the task will proceed normally.

        :return: `True` if everything is OK, `False` otherwise. Defaults to `True`.
        :rtype: `bool`
        """

        return True

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        pass
