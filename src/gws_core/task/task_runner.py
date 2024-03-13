

from typing import Dict, Type

from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import (
    BasicMessageObserver, LoggerMessageObserver, MessageObserver)

from ..config.config_params import ConfigParams
from ..config.config_types import ConfigParamsDict
from ..io.io_exception import InvalidOutputsException
from ..io.io_specs import InputSpecs, OutputSpecs
from ..progress_bar.progress_bar import ProgressBar
from ..resource.resource import Resource
from ..task.task import CheckBeforeTaskResult, Task
from ..task.task_io import TaskInputs, TaskOutputs


class TaskRunner():
    """This is used to run a Task. It can be used in unit test to test a Task.

    Simply provide the task type, config params and inputs. then you can call the run method to test your task
    and check outputs

    :raises MissingInputResourcesException: [description]
    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """

    _task_type: Type[Task]
    _input_specs: InputSpecs
    _output_specs: OutputSpecs
    _inputs: Dict[str, Resource]
    _outputs: TaskOutputs

    _task: Task
    _message_dispatcher: MessageDispatcher

    _config_model_id: str = None

    _config_params: ConfigParams = None

    def __init__(self, task_type: Type[Task], params: ConfigParamsDict = None,
                 inputs: Dict[str, Resource] = None,
                 config_model_id: str = None,
                 input_specs: InputSpecs = None,
                 output_specs: OutputSpecs = None):
        self._task_type = task_type

        if inputs is None:
            self._inputs = {}
        else:
            self._inputs = inputs

        self._task = None
        self._outputs = None
        self._config_model_id = config_model_id

        self._message_dispatcher = MessageDispatcher()
        self.add_observer(LoggerMessageObserver())

        self._input_specs = input_specs or self._task_type.input_specs
        self._output_specs = output_specs or self._task_type.output_specs

        self._build_config(params)

    def check_before_run(self) -> CheckBeforeTaskResult:
        """This method check the config and inputs and then execute the check before run of the task

        :return: [description]
        :rtype: CheckBeforeTaskResult
        """
        # get the input without checking them
        inputs: TaskInputs = self._get_and_check_input()

        task: Task = self._get_task_instance()
        task._status_ = 'CHECK_BEFORE_RUN'

        result = None
        try:
            result = task.check_before_run(self._config_params, inputs)
        except KeyError as exception:
            raise Exception(f"KeyError : {str(exception)}")
        except Exception as exception:
            self.force_dispatch_waiting_messages()
            raise exception

        self.force_dispatch_waiting_messages()
        return result

    def run(self) -> TaskOutputs:
        """This method, checks the config, inputs and then run the task

        :return: [description]
        :rtype: TaskOutputs
        """
        inputs: TaskInputs = self._get_and_check_input()
        task: Task = self._get_task_instance()
        task._status_ = 'RUN'

        try:
            task_outputs: TaskOutputs = task.run(self._config_params, inputs)
        except KeyError as exception:
            raise Exception(f"KeyError : {str(exception)}")
        except Exception as exception:
            self.force_dispatch_waiting_messages()
            raise exception from exception

        self.force_dispatch_waiting_messages()
        return self._check_outputs(task_outputs)

    def run_after_task(self) -> None:
        task: Task = self._get_task_instance()
        task._status_ = 'RUN_AFTER_TASK'

        try:
            task.run_after_task()
        except KeyError as exception:
            raise Exception(f"KeyError : {str(exception)}")
        except Exception as exception:
            self.force_dispatch_waiting_messages()
            raise exception

        self.force_dispatch_waiting_messages()

    def set_input(self, input_name: str, resource: Resource) -> None:
        self._inputs[input_name] = resource

    def get_output(self, output_name: str) -> Resource:
        return self._outputs[output_name]

    def get_outputs(self) -> TaskOutputs:
        return self._outputs

    def _get_task_instance(self) -> Task:
        # create the task only if it doesn't exists
        if self._task is None:
            self._task = self._task_type()
            self._task.__set_message_dispatcher__(self._message_dispatcher)

            try:
                self._task.init()
            except Exception as exception:
                self.force_dispatch_waiting_messages()
                raise exception

        return self._task

    def _get_and_check_input(self) -> TaskInputs:
        """Check and convert input to TaskInputs
        :rtype: TaskInputs
        """
        return self._input_specs.check_and_build_inputs(self._inputs)

    def _build_config(self, config) -> ConfigParams:
        """Check and convert the config to ConfigParams

        :return: [description]
        :rtype: ConfigParams
        """
        if isinstance(config, ConfigParams):
            config = dict(config)

        if config is None:
            config = {}

        if self._config_params is None:
            self._config_params = ParamSpecHelper.build_config_params(self._task_type.config_specs,
                                                                      config)
            self._config_params.set_config_model_id(self._config_model_id)
        return self._config_params

    def _check_outputs(self, task_outputs: TaskOutputs) -> TaskOutputs:
        """Method that check if the task outputs

        :param task_outputs: outputs to check
        :type task_outputs: TaskOutputs
        :raises InvalidOutputException: raised if the output are invalid
        """

        result = self._output_specs.check_and_build_outputs(task_outputs)

        self._outputs = result.outputs

        if result.error and len(result.error) > 0:
            raise InvalidOutputsException(result.error)

        return self._outputs

    def set_progress_bar(self, progress_bar: ProgressBar) -> None:
        self._message_dispatcher.attach_progress_bar(progress_bar)

    def add_log_observer(self) -> BasicMessageObserver:
        """Method to create an observer and attached it to the task.
        The log will be available in the retuned BasicMessageObserver.
        This can be useful for testings

        :return: _description_
        :rtype: BasicMessageObserver
        """
        observer = BasicMessageObserver()
        self._message_dispatcher.attach(observer)
        return observer

    def add_observer(self, observer: MessageObserver) -> None:
        """Method to create an observer and attached it to the task.
        The log will be available in the retuned BasicMessageObserver.
        This can be useful for testings

        :return: _description_
        :rtype: BasicMessageObserver
        """
        self._message_dispatcher.attach(observer)

    def force_dispatch_waiting_messages(self) -> None:
        self._message_dispatcher.force_dispatch_waiting_messages()

    def get_task(self) -> Task:
        return self._task
