# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Literal, Optional, Type, TypedDict, final

from gws_core.model.typing_register_decorator import typing_registrator

from ..config.config_types import ConfigParams, ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io_spec_helper import InputSpecs, OutputSpecs
from ..process.process import Process
from ..progress_bar.progress_bar import ProgressBar, ProgressBarMessageType
from ..resource.resource import Resource
from ..task.task_io import TaskInputs, TaskOutputs

# Typing names generated for the class Task
CONST_TASK_TYPING_NAME = "TASK.gws_core.Task"


class CheckBeforeTaskResult(TypedDict, total=False):
    # If True, everything is ok
    # If False the task will not be executed after this check it might be run latter if they are some SKippableIn inputs
    # If all the input values were provided and the check retuns False. the task will endup in error because it won't be run
    result: bool

    # If False a message can be provided to log the error message if the task will not be called
    message: Optional[str]


@typing_registrator(unique_name="Task", object_type="TASK", hide=True)
class Task(Process):

    input_specs: InputSpecs = {}
    output_specs: OutputSpecs = {}
    config_specs: ConfigSpecs = {}

    # Instance of the progress bar, do not use
    _progress_bar_: ProgressBar
    # Current status of the task, do not update
    _status_: Literal['CHECK_BEFORE_RUN', 'RUN', 'RUN_AFTER_TASK']

    def __init__(self):
        """
        Constructor
        """

        super().__init__()

        # check that the class level property _typing_name is set
        if self._typing_name is None:
            raise BadRequestException(
                f"The task {self.full_classname()} is not decorated with @task_decorator, it can't be instantiate. Please decorate the task class with @task_decorator")
        self._progress_bar_ = None
        self._status_ = None

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        """
        This can be overwritten to perform custom check before running task.
        See doc of CheckBeforeTaskResult for more information
        :rtype: `bool`
        """

        return {"result": True, "message": None}

    @abstractmethod
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """This must be overiwritten to perform the task of the task.

        This is where most of your code must go

        :param params: [description]
        :type params: Config
        :param inputs: [description]
        :type inputs: Input
        :param outputs: [description]
        :type outputs: Output
        """

    async def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

    @final
    def get_default_output_spec_type(self, spec_name: str) -> Type[Resource]:
        if not self.output_specs:
            return None

        if spec_name not in self.output_specs:
            raise BadRequestException(f"The output spec does not have a spec named '{spec_name}'")

        return self.output_specs[spec_name].get_default_resource_type()

    @final
    def update_progress_value(self, value: float, message: str = None) -> None:
        """Update the progress value

        :param value: value between 0 and 100 of the progress
        :type value: float
        :param message: if provided a message is stored on the progress
        :type message: str
        """
        if self._status_ != 'RUN':
            raise BadRequestException("The progress value can only be updated in run method")

        self._progress_bar_.update_progress(value=value, message=message)

    @final
    def log_message(self, message: str, type_: ProgressBarMessageType = ProgressBarMessageType.INFO) -> None:
        """Store a message in the progress

        :param message: message to store in the progress
        :type message: str
        """

        self._progress_bar_.add_message(message=message, type_=type_)

    @final
    def log_info_message(self, message: str):
        self.log_message(message, ProgressBarMessageType.INFO)

    @final
    def log_success_message(self, message: str):
        self.log_message(message, ProgressBarMessageType.SUCCESS)

    @final
    def log_error_message(self, message: str):
        self.log_message(message, ProgressBarMessageType.ERROR)

    @final
    def log_warning_message(self, message: str):
        self.log_message(message, ProgressBarMessageType.WARNING)
