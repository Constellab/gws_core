# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from ..config.config import Config
from ..config.config_types import ConfigParams, ConfigParamsDict, ParamValue
from ..io.io_exception import (InvalidInputsException, InvalidOutputsException,
                               MissingInputResourcesException)
from ..io.io_spec import IOSpecClass, IOSpecsHelper, OutputSpec
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
    _progress_bar: ProgressBar

    def __init__(self, task_type: Type[Task], params: ConfigParamsDict = None, inputs: Dict[str, Resource] = None):
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
        self._progress_bar = None

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

        return task.check_before_run(config_params, inputs)

    async def run(self) -> TaskOutputs:
        """This method, checks the config, inputs and then run the task

        :return: [description]
        :rtype: TaskOutputs
        """
        config_params: ConfigParams = self._get_and_check_config()
        inputs: TaskInputs = self._get_and_check_input()
        task: Task = self._get_task_instance()
        task._status_ = 'RUN'

        task_outputs: TaskOutputs = await task.run(config_params, inputs)

        return self._check_outputs(task_outputs)

    async def run_after_task(self) -> None:
        task: Task = self._get_task_instance()
        task._status_ = 'RUN_AFTER_TASK'

        await task.run_after_task()

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

            if self._progress_bar is None:
                self._progress_bar = ProgressBar()

            self._task._progress_bar_ = self._progress_bar

        return self._task

    def _get_and_check_input(self) -> TaskInputs:
        """Check and convert input to TaskInputs]
        :rtype: TaskInputs
        """
        missing_resource: List[str] = []
        invalid_input_text: str = ''

        task_io: TaskInputs = TaskInputs()

        input_specs: Dict[str, IOSpecClass] = self._get_task_inputs_specs()

        for key, spec in input_specs.items():
            # If the resource is None
            if key not in self._inputs or self._inputs[key] is None:
                # If the resource is empty and the spec not optional, add an error
                if not spec.is_optional():
                    missing_resource.append(key)
                continue

            resource: Resource = self._inputs[key]
            if not spec.is_compatible_with_type(type(resource)):
                invalid_input_text = invalid_input_text + \
                    f"The input '{key}' of type '{resource}' is not a compatble with the corresponding input spec."

            task_io[key] = resource

        if len(missing_resource) > 0:
            raise MissingInputResourcesException(port_names=missing_resource)

        if invalid_input_text and len(invalid_input_text) > 0:
            raise InvalidInputsException(invalid_input_text)

        return task_io

    def _get_task_inputs_specs(self) -> Dict[str, IOSpecClass]:
        specs: Dict[str, IOSpecClass] = {}

        for key, spec in self._task_type.input_specs.items():
            specs[key] = IOSpecClass(spec)
        return specs

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

        for key, spec in self._task_type.output_specs.items():
            spec_class = IOSpecClass(spec)

            # If the resource for the output port was provided
            if key in task_outputs:
                resource: Resource = task_outputs[key]

                error = self._check_output(resource, spec_class, key)
                if error is not None and len(error) > 0:
                    error_text = error_text + error

                # save the resource event if there is an error
                verified_outputs[key] = resource

            # If the output is missing
            else:
                if not spec_class.is_optional():
                    error_text = error_text + f"The output '{key}' was not provided."

        # save the verified outputs before thowing an error
        self._outputs = verified_outputs

        if error_text and len(error_text) > 0:
            raise InvalidOutputsException(error_text)

        return self._outputs

    def _check_output(self, output_resource: Resource, spec: IOSpecClass, key: str) -> str:
        """Method to check a output resource, return str if there is an error with the resource
        """

        if output_resource is None:
            # No error if the spec is optional
            if spec.is_optional():
                return None
            return f"The output '{key}' is None."

        if not isinstance(output_resource, Resource):
            return f"The output '{key}' of type '{type(output_resource)}' is not a resource. It must extend the Resource class"

        # Check resource is compatible with specs
        if not spec.is_compatible_with_type(type(output_resource)):
            return f"The output '{key}' of type '{type(output_resource)}' is not a compatble with the corresponding output spec."

        # Check that the resource is well formed
        try:
            error = output_resource.check_resource()

            if error is not None and len(error) > 0:
                return error

        except Exception as err:
            return f"Error during the key of the output resource '{key}'. Error : {str(err)}"

        return None

    def set_progress_bar(self, progress_bar: ProgressBar) -> None:
        self._progress_bar = progress_bar
