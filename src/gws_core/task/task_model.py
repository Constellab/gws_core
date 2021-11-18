# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import zlib
from typing import List, Type

from gws_core.core.decorator.transaction import transaction

from ..config.config_types import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.utils.logger import Logger
from ..io.io_exception import InvalidOutputException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import typing_registrator
from ..process.process_exception import (CheckBeforeTaskStopException,
                                         ProcessRunException)
from ..process.process_model import ProcessModel
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskInputs, TaskOutputs
from .task import CheckBeforeTaskResult, Task


@typing_registrator(unique_name="Task", object_type="MODEL", hide=True)
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
            self._inputs.create_port(k, task_type.input_specs[k])

        # set the resources to the ports
        self._init_inputs_from_data()

        # create the output ports from the Task output specs
        for k in task_type.output_specs:
            self._outputs.create_port(k, task_type.output_specs[k])

        # set the resources to the ports
        self._init_outputs_from_data()

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

    def _create_task_instance(self) -> Task:
        return self._get_process_type()()

    def is_protocol(self) -> bool:
        return False
    ################################# MODEL METHODS #############################

    def save_full(self) -> 'TaskModel':
        self.config.save()
        self.progress_bar.save()
        return self.save()

    # -- A --
    @transaction()
    def archive(self, archive: bool, archive_resources=True) -> 'TaskModel':
        """
        Archive the process
        """

        if self.is_archived == archive:
            return self

        super().archive(archive)

        # -> try to archive the config if possible!
        self.config.archive(archive)
        if archive_resources:
            for resource in self.resources:
                resource.archive(archive)

        return self

    @property
    def resources(self) -> List[ResourceModel]:
        if not self.id:
            return []

        return list(ResourceModel.select().where(ResourceModel.task_model == self))

    ################################# RUN #############################

    async def _run(self) -> None:
        """
        Run the task and save its state in the database.
        """
        # Create the task instance to run the task
        task: Task = self._create_task_instance()

        # Set the progress bar
        task._progress_bar_ = self.progress_bar
        task._status_ = 'CHECK_BEFORE_RUN'

        # Get simpler object for to run the task
        config_params: ConfigParams = self.config.get_and_check_values()
        task_inputs: TaskInputs = self.inputs.get_and_check_task_inputs()

        check_result: CheckBeforeTaskResult
        try:
            check_result = task.check_before_run(
                config_params, task_inputs)
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during check before task') from err

        # If the check before task retuned False
        if isinstance(check_result, dict) and check_result.get('result') is False:
            if self.inputs.all_connected_port_values_provided():
                raise CheckBeforeTaskStopException(message=check_result.get('message'))
            else:
                return

        await self._run_before_task()
        # run the task
        await self._run_task(task=task, config_params=config_params, task_inputs=task_inputs)

        # execute the run after task method
        try:
            task._status_ = 'RUN_AFTER_TASK'
            await task.run_after_task()
        except Exception as err:
            if not isinstance(err, ProcessRunException):
                Logger.log_exception_stack_trace(err)
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during check after task') from err

        await self._run_after_task()

    async def _run_task(self, task: Task, config_params: ConfigParams, task_inputs: TaskInputs) -> None:
        """
        Run the task and save its state in the database.
        """

        task_outputs: TaskOutputs
        task._status_ = 'RUN'

        try:
            # Run the task task
            task_outputs = await task.run(config_params, task_inputs)
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during task') from err

        if task_outputs is None:
            task_outputs = {}

        if not isinstance(task_outputs, dict):
            raise BadRequestException('The task output is not a dictionary')

        self._check_and_save_outputs(task_outputs)

    def _check_and_save_outputs(self, task_outputs: TaskOutputs) -> None:

        error_text: str = ''

        for key, port in self.outputs.ports.items():
            resource_model: ResourceModel

            # If the resource for the output port was provided
            if key in task_outputs:

                resource: Resource = task_outputs[key]

                if not isinstance(resource, Resource):
                    error_text = f"The output '{key}' of type '{type(resource)}' is not a resource. It must extend the Resource class"

                if not port.resource_type_is_compatible(type(resource)):
                    error_text = f"The output '{key}' of type '{type(resource)}' is not a compatble with the output specs."

                if port.is_constant_out:
                    # If the port is mark as unmodified, we don't create a new resource
                    # We use the same resource
                    resource_model = ResourceModel.get_by_uri_and_check(resource._model_uri)
                else:
                    # create the resource model from the resource
                    resource_model = ResourceModel.from_resource(resource)

                    # Add info and save resource model
                    resource_model.experiment = self.experiment
                    resource_model.task_model = self
                    resource_model.save_full()

            else:
                error_text = error_text + f"The output '{key}' was not provided."
                resource_model = None

            # save the resource model into the output's port (even if it's None)
            port.resource_model = resource_model

        if error_text and len(error_text) > 0:
            raise InvalidOutputException(error_text)

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

        if "inputs" in _json:
            del _json["inputs"]
        if "outputs" in _json:
            del _json["outputs"]

        return _json
