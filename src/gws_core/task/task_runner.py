# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver
from gws_core.core.utils.logger import Logger
from gws_core.io.io_spec import OutputSpec

from ..config.config import Config
from ..config.config_types import ConfigParams, ConfigParamsDict
from ..config.param.param_types import ParamValue
from ..io.io_exception import (InvalidInputsException, InvalidOutputsException,
                               MissingInputResourcesException)
from ..io.io_spec_helper import InputSpecs, OutputSpecs
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
    _params: ConfigParamsDict
    _inputs: Dict[str, Resource]
    _outputs: TaskOutputs

    _task: Task
    _message_dispatcher: MessageDispatcher

    _config_model_id: str = None

    def __init__(self, task_type: Type[Task], params: ConfigParamsDict = None, inputs: Dict[str, Resource] = None,
                 message_dispatcher: MessageDispatcher = None, config_model_id: str = None):
        self._task_type = task_type

        if params is None:
            self._params = {}
        else:
            self._params = params

        if inputs is None:
            self._inputs = {}
        else:
            self._inputs = inputs

        self._task = None
        self._outputs = None
        self._config_model_id = config_model_id

        if message_dispatcher is None:
            self._message_dispatcher = MessageDispatcher()
        else:
            self._message_dispatcher = message_dispatcher

    def check_before_run(self) -> CheckBeforeTaskResult:
        """This method check the config and inputs and then execute the check before run of the task

        :return: [description]
        :rtype: CheckBeforeTaskResult
        """
        config_params: ConfigParams = self._get_and_check_config()

        # get the input without checking them
        inputs: TaskInputs = self._get_and_check_input()

        task: Task = self._get_task_instance()
        task._status_ = 'CHECK_BEFORE_RUN'

        result = None
        try:
            result = task.check_before_run(config_params, inputs)
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
        config_params: ConfigParams = self._get_and_check_config()
        inputs: TaskInputs = self._get_and_check_input()
        task: Task = self._get_task_instance()
        task._status_ = 'RUN'

        try:
            task_outputs: TaskOutputs = task.run(config_params, inputs)
        except KeyError as exception:
            raise Exception(f"KeyError : {str(exception)}")
        except Exception as exception:
            self.force_dispatch_waiting_messages()
            raise exception

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

    def set_param(self, param_name: str, config_param: ParamValue) -> None:
        self._params[param_name] = config_param

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
            self._task._config_model_id = self._config_model_id

            try:
                self._task.init()
            except Exception as exception:
                self.force_dispatch_waiting_messages()
                raise exception

        return self._task

    def _get_and_check_input(self) -> TaskInputs:
        """Check and convert input to TaskInputs]
        :rtype: TaskInputs
        """
        missing_resource: List[str] = []
        invalid_input_text: str = ''

        task_io: TaskInputs = TaskInputs()

        for key, spec in self._get_task_inputs_specs().items():
            # If the resource is None
            if key not in self._inputs or self._inputs[key] is None:
                # If the resource is empty and the spec not optional, add an error
                if not spec.is_optional:
                    missing_resource.append(key)
                continue

            resource: Resource = self._inputs[key]
            if not spec.is_compatible_with_resource_type(type(resource)):
                invalid_input_text = invalid_input_text + \
                    f"The input '{key}' of type '{resource._typing_name}' is not a compatible with the corresponding input spec."

            task_io[key] = resource

        if len(missing_resource) > 0:
            raise MissingInputResourcesException(port_names=missing_resource)

        if invalid_input_text and len(invalid_input_text) > 0:
            raise InvalidInputsException(invalid_input_text)

        return task_io

    def _get_task_inputs_specs(self) -> InputSpecs:
        return self._task_type.input_specs

    def _get_task_outputs_specs(self) -> OutputSpecs:
        return self._task_type.output_specs

    def _get_and_check_config(self) -> ConfigParams:
        """Check and convert the config to ConfigParams

        :return: [description]
        :rtype: ConfigParams
        """
        config: Config = Config()
        config.set_specs(self._task_type.config_specs)
        config.set_values(self._params)
        return config.get_and_check_values()

    def _check_outputs(self, task_outputs: TaskOutputs) -> TaskOutputs:
        """Method that check if the task outputs

        :param task_outputs: outputs to check
        :type task_outputs: TaskOutputs
        :raises InvalidOutputException: raised if the output are invalid
        """

        if task_outputs is None:
            task_outputs = {}

        if not isinstance(task_outputs, dict):
            raise Exception('The task output is not a dictionary')

        error_text: str = ''

        verified_outputs: TaskOutputs = {}

        for key, spec in self._get_task_outputs_specs().items():

            # handle the case where the output is None
            if key not in task_outputs or task_outputs[key] is None:
                if not spec.is_optional:
                    text = "was not provided" if key not in task_outputs else "is None"
                    error_text = error_text + \
                        f"The output '{key}' {text}."
                continue

            # If the resource for the output port was provided
            if key in task_outputs:
                resource: Resource = task_outputs[key]

                error = self._check_output(resource, spec, key)
                if error is not None and len(error) > 0:
                    error_text = error_text + error

                # save the resource event if there is an error
                if isinstance(resource, Resource):
                    verified_outputs[key] = resource

        # save the verified outputs before thowing an error
        self._outputs = verified_outputs

        if error_text and len(error_text) > 0:
            raise InvalidOutputsException(error_text)

        return self._outputs

    def _check_output(self, output_resource: Resource, spec: OutputSpec, key: str) -> str:
        """Method to check a output resource, return str if there is an error with the resource
        """

        if not isinstance(output_resource, Resource):
            return f"The output '{key}' of type '{type(output_resource)}' is not a resource. It must extend the Resource class"

        # Check resource is compatible with specs
        if not spec.is_compatible_with_resource_type(type(output_resource)):
            return f"The output '{key}' of type '{type(output_resource)}' is not a compatble with the corresponding output spec."

        # Check that the resource is well formed
        try:
            error = output_resource.check_resource()

            if error is not None and len(error) > 0:
                return error

        except Exception as err:
            Logger.log_exception_stack_trace(err)
            return f"Error during the key of the output resource '{key}'. Error : {str(err)}"

        return None

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

    def force_dispatch_waiting_messages(self) -> None:
        self._message_dispatcher.force_dispatch_waiting_messages()

    def get_task(self) -> Task:
        return self._task
