# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import zlib
from typing import Dict, Type

from ..config.config_params import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import typing_registrator
from ..process.process_exception import (CheckBeforeTaskStopException,
                                         ProcessRunException)
from ..process.process_model import ProcessModel
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskInputs, TaskOutputs
from .task import CheckBeforeTaskResult, Task


@typing_registrator(unique_name="Task", object_type="GWS_CORE", hide=True)
class TaskModel(ProcessModel):
    """
    Task model class.

    :property input_specs: The specs of the input
    :type input_specs: dict
    :property output_specs: The specs of the output
    :type output_specs: dict
    :property config_specs: The specs of the config
    :type config_specs: dict
    """

    _table_name = 'gws_task'

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """

        super().__init__(*args, **kwargs)

        if self.process_typing_name is not None:
            self._init_io()

    def _init_io(self):
        task_type: Type[Task] = self._get_process_type()

        # create the input ports from the Task input specs
        for k in task_type.input_specs:
            self._input.create_port(k, task_type.input_specs[k])

        # set the resources to the ports
        self._init_input_from_data()

        # create the output ports from the Task output specs
        for k in task_type.output_specs:
            self._output.create_port(k, task_type.output_specs[k])

        # set the resources to the ports
        self._init_output_from_data()

    # -- C --

    def create_source_zip(self):
        """
        Returns the zipped code source of the task
        """

        # /:\ Use the true object type (self.type)
        model_t: Type[TaskModel] = TypingManager.get_type_from_name(
            self.process_typing_name)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())

    def set_task_type(self, typing_name: str) -> None:
        self.process_typing_name = typing_name
        self._init_io()

    # -- D --

    def _create_task_instance(self) -> Task:
        return self._get_process_type()()

    async def _run(self) -> None:
        """
        Run the task and save its state in the database.
        """
        # Create the task instance to run the task
        task: Task = self._create_task_instance()

        # Get simpler object for to run the task
        config_params: ConfigParams = self.config.get_and_check_params()
        task_inputs: TaskInputs = self.input.get_and_check_task_inputs()

        check_result: CheckBeforeTaskResult
        try:
            check_result = task.check_before_run(
                config=config_params, inputs=task_inputs)
        except Exception as err:
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during check before task') from err

        # If the check before task retuned False
        if isinstance(check_result, dict) and check_result.get('result') is False:
            if self.input.all_connected_port_values_provided():
                raise CheckBeforeTaskStopException(message=check_result.get('message'))
            else:
                return

        await self._run_before_task()
        # run the task
        await self._run_task(task=task, config_params=config_params, task_inputs=task_inputs)
        await self._run_after_task()

    async def _run_task(self, task: Task, config_params: ConfigParams, task_inputs: TaskInputs) -> None:
        """
        Run the task and save its state in the database.
        """

        # Set the progress bar
        task.__progress_bar__ = self.progress_bar

        task_output: TaskOutputs

        try:
            # Run the task task
            task_output = await task.run(config=config_params, inputs=task_inputs)
        except Exception as err:
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during task') from err

        if task_output is None:
            task_output = {}

        if not isinstance(task_output, dict):
            raise BadRequestException('The task output is not a dictionary')

        for key, port in self.output.ports.items():
            resource_model: ResourceModel

            # If the resource for the output port was provided
            if key in task_output:

                resource: Resource = task_output[key]

                if not isinstance(resource, Resource):
                    raise BadRequestException(
                        f"The output '{key}' of type '{type(resource)}' is not a resource. It must extend the Resource class")

                # Get the type of resource model to create for this resource
                resource_model_type: Type[ResourceModel] = resource.get_resource_model_type()
                if not issubclass(resource_model_type, ResourceModel):
                    raise BadRequestException(
                        f"The method get_resource_model_type of resource {resource.classname()} did not return a type that extend ResourceModel")

                if port.is_unmodified_out:
                    # If the port is mark as resource existing, we don't create a new resource
                    # We use the same resource
                    resource_model = TypingManager.get_object_with_typing_name_and_uri(
                        typing_name=resource_model_type._typing_name, uri=resource._model_uri)
                else:
                    # create the resource model from the resource
                    resource_model = resource_model_type.from_resource(resource)

            else:
                resource_model = None

            # save the resource model into the output's port (even if it's None)
            port.resource_model = resource_model

    async def _run_after_task(self):

        # Save the generated resource
        res: Dict[str, ResourceModel] = self.output.get_resources()
        for resource in res.values():
            if resource is not None and not resource.is_saved():
                resource.experiment = self.experiment
                resource.task = self
                resource.save()
        await super()._run_after_task()

    def is_protocol(self) -> bool:
        return False

    def save_full(self) -> 'TaskModel':
        self.config.save()
        self.progress_bar.save()
        return self.save()

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json: dict = super().data_to_json(deep=deep)

        if "input" in _json:
            del _json["input"]
        if "output" in _json:
            del _json["output"]

        return _json
