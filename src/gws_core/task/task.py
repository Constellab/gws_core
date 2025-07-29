

from abc import abstractmethod
from typing import List, Literal, Optional, Type, final

from typing_extensions import TypedDict

from gws_core.core.classes.observer.dispatched_message import DispatchedMessage
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.model.typing_register_decorator import typing_registrator
from gws_core.model.typing_style import TypingStyle

from ..config.config_params import ConfigParams
from ..config.config_specs import ConfigSpecs
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.io_specs import InputSpecs, OutputSpecs
from ..process.process import Process
from ..resource.resource import Resource
from ..task.task_io import TaskInputs, TaskOutputs

# Typing names generated for the class Task
CONST_TASK_TYPING_NAME = "TASK.gws_core.Task"


class CheckBeforeTaskResult(TypedDict, total=False):
    # If True, everything is ok
    # If False the task will not be executed after this check it might be run later if they are some SKippableIn inputs
    # If all the input values were provided and the check retuns False. the task will endup in error because it won't be run
    result: bool

    # If False a message can be provided to log the error message if the task will not be called
    message: Optional[str]


@typing_registrator(unique_name="Task", object_type="TASK", hide=True,
                    style=TypingStyle.default_task())
class Task(Process):

    input_specs: InputSpecs = InputSpecs({})
    output_specs: OutputSpecs = OutputSpecs({})
    config_specs: ConfigSpecs = ConfigSpecs({})

    # Message dispatcher used to log messages of the task
    message_dispatcher: MessageDispatcher

    # set this during the run of the task to apply a dynamic style to the task
    # This overrides the style set by the task_decorator
    style: TypingStyle

    # Current status of the task, do not update
    __status__: Literal['CHECK_BEFORE_RUN', 'RUN', 'RUN_AFTER_TASK']

    # list of temporary directories created by the task to be deleted after the task is run
    __temp_dirs__: List[str]

    # The scenario id and task id that run the task, do not update
    # This is only provided when the task is run by a scenario
    __scenario_id__: str
    __task_id__: str

    def __init__(self):
        """
        Constructor, please do not overwrite this method, use the init method instead
        Leave the constructor without parameters
        """

        super().__init__()

        # check that the class level property typing_name is set
        if self.get_typing_name() is None:
            raise BadRequestException(
                f"The task {self.full_classname()} is not decorated with @task_decorator, it can't be instantiate. Please decorate the task class with @task_decorator")
        self.__status__ = None
        self.message_dispatcher = None
        self.style = None
        self.__temp_dirs__ = []
        self.__scenario_id__ = None

    def init(self) -> None:
        """
        This can be overwritten to perform custom initialization of the task.
        This method is called just after the __init__ and before the check_before_run method
        """

    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        """
        This can be overwritten to perform custom check before running task.
        See doc of CheckBeforeTaskResult for more information
        :rtype: `bool`
        """

        return {"result": True, "message": None}

    @abstractmethod
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """This must be overiwritten to perform the task of the task.

        This is where most of your code must go

        :param params: [description]
        :type params: Config
        :param inputs: [description]
        :type inputs: Input
        :param outputs: [description]
        :type outputs: Output
        """

    def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resources are saved. This method is useful to delete temporary objects (like files) to clear the server after the task is run.
        """
        # delete temporary directories
        for tmp_dir in self.__temp_dirs__:
            self.log_debug_message(f"Deleting temporary directorie '{tmp_dir}'")
            FileHelper.delete_dir(tmp_dir)

    @final
    def get_default_output_spec_type(self, spec_name: str) -> Type[Resource]:
        if not self.output_specs:
            return None

        if not self.output_specs.has_spec(spec_name):
            raise BadRequestException(
                f"The output spec does not have a spec named '{spec_name}'")

        return self.output_specs.get_spec(spec_name).get_default_resource_type()

    @final
    def update_progress_value(self, value: float, message: str) -> None:
        """Update the progress value

        :param value: value between 0 and 100 of the progress
        :type value: float
        :param message: if provided a message is stored on the progress
        :type message: str
        """
        if self.__status__ != 'RUN':
            raise BadRequestException(
                "The progress value can only be updated in run method")

        self.message_dispatcher.notify_progress_value(
            progress=value, message=message)

    @final
    def log_message(self, message: str, type_: MessageLevel) -> None:
        """Store a message in the progress

        :param message: message to store in the progress
        :type message: str
        """
        dispatched_message = DispatchedMessage(status=type_, message=message)

        self.message_dispatcher.notify_message(dispatched_message)

    @final
    def log_debug_message(self, message: str):
        self.log_message(message, MessageLevel.DEBUG)

    @final
    def log_info_message(self, message: str):
        self.log_message(message, MessageLevel.INFO)

    @final
    def log_success_message(self, message: str):
        self.log_message(message, MessageLevel.SUCCESS)

    @final
    def log_error_message(self, message: str):
        self.log_message(message, MessageLevel.ERROR)

    @final
    def log_warning_message(self, message: str):
        self.log_message(message, MessageLevel.WARNING)

    @final
    def __set_message_dispatcher__(self, message_dispatcher: MessageDispatcher) -> None:
        self.message_dispatcher = message_dispatcher

    @final
    def __set_scenario_id__(self, scenario_id: str) -> None:
        self.__scenario_id__ = scenario_id

    @final
    def get_scenario_id(self) -> str:
        return self.__scenario_id__

    @final
    def __set_task_id__(self, task_id: str) -> None:
        self.__task_id__ = task_id

    @final
    def get_task_id(self) -> str:
        return self.__task_id__

    @final
    @classmethod
    def get_input_specs(cls) -> InputSpecs:
        return cls.input_specs

    @final
    @classmethod
    def get_output_specs(cls) -> OutputSpecs:
        return cls.output_specs

    def create_tmp_dir(self) -> str:
        """
        Create a temporary directory.
        This directory will be deleted after the task is run.
        Output file or folder are moved out of this directory before it is deleted.
        :param prefix: prefix of the directory
        :return: path of the created directory
        """
        tmp_dir = Settings.make_temp_dir()
        self.__temp_dirs__.append(tmp_dir)
        return tmp_dir

    ############################################### SYSTEM METHODS ####################################################

    @final
    def __set_status__(self, status: Literal['CHECK_BEFORE_RUN', 'RUN', 'RUN_AFTER_TASK']) -> None:
        """Set the model id of the resource
        This method is called by the system when the resource is created,
        you should not call this method yourself

        :param model_id: model id
        :type model_id: str
        """
        self.__status__ = status
