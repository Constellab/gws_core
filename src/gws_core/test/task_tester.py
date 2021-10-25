# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from ..config.config import Config
from ..config.config_types import ConfigParams, ConfigParamsDict, ParamValue
from ..io.io_exception import MissingInputResourcesException
from ..io.io_spec import IOSpecClass
from ..progress_bar.progress_bar import ProgressBar
from ..resource.resource import Resource
from ..task.task import CheckBeforeTaskResult, Task
from ..task.task_io import TaskInputs, TaskOutputs


class TaskTester():
    """This class is meant to be used in unit tests to test a Task

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

    def check_before_run(self) -> CheckBeforeTaskResult:
        config_params: ConfigParams = self._get_and_check_config()

        # get the input without checking them
        inputs: TaskInputs = TaskInputs()
        for key, item in self._inputs.items():
            inputs[key] = item

        task: Task = self._instantiate_task()

        return task.check_before_run(config_params, inputs)

    async def run(self) -> TaskOutputs:
        """This method, checks the config, inputs and then run the task

        :return: [description]
        :rtype: TaskOutputs
        """
        config_params: ConfigParams = self._get_and_check_config()
        inputs: TaskInputs = self._get_and_check_input()
        task: Task = self._instantiate_task()

        self._outputs = await task.run(config_params, inputs)
        return self._outputs

    def set_param(self, param_name: str, config_param: ParamValue) -> None:
        self._params[param_name] = config_param

    def set_input(self, input_name: str, resource: Resource) -> None:
        self._inputs[input_name] = resource

    def get_output(self, output_name: str) -> Resource:
        return self._outputs[output_name]

    def _instantiate_task(self) -> Task:
        task: Task = self._task_type()

        # set the progress bar
        task.__progress_bar__ = ProgressBar()
        return task

    def _get_and_check_input(self) -> TaskInputs:
        """Check and convert input to TaskInputs]
        :rtype: TaskInputs
        """
        missing_resource: List[str] = []
        task_io: TaskInputs = TaskInputs()

        input_specs: Dict[str, IOSpecClass] = self._get_task_inputs_specs()

        for key, spec in input_specs.items():
            # If the resource is None
            if key not in self._inputs or self._inputs[key] is None:
                # If the resource is empty and the spec not optional, add an error
                if not spec.is_optional():
                    missing_resource.append(key)
                continue

            task_io[key] = self._inputs[key]

        if len(missing_resource) > 0:
            raise MissingInputResourcesException(port_names=missing_resource)

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
