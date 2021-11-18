# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import zlib
from typing import Dict, List, Type

from ..config.config_types import ConfigParamsDict
from ..core.decorator.transaction import transaction
from ..core.utils.logger import Logger
from ..io.io_exception import InvalidOutputsException
from ..io.port import Port
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import typing_registrator
from ..process.process_exception import (CheckBeforeTaskStopException,
                                         ProcessRunException)
from ..process.process_model import ProcessModel
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskOutputs
from .task import CheckBeforeTaskResult, Task
from .task_runner import TaskRunner


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
        if not self.is_saved():
            return []

        return list(ResourceModel.select().where(ResourceModel.task_model == self))

    ################################# RUN #############################

    async def _run(self) -> None:
        """
        Run the task and save its state in the database.
        """

        # build the task tester
        params: ConfigParamsDict = self.config.get_values()
        inputs: Dict[str, Resource] = self.inputs.get_resources(new_instance=True)

        task_runner: TaskRunner = TaskRunner(self._get_process_type(), params, inputs)
        task_runner.set_progress_bar(self.progress_bar)

        check_result: CheckBeforeTaskResult
        try:
            check_result = task_runner.check_before_run()
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
        await self._run_task(task_runner)

        # execute the run after task method
        try:
            await task_runner.run_after_task()
        except Exception as err:
            if not isinstance(err, ProcessRunException):
                Logger.log_exception_stack_trace(err)
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during check after task') from err

        await self._run_after_task()

    async def _run_before_task(self) -> None:
        await super()._run_before_task()

        # Store all the resources user as input for this taks
        self.save_input_resources()

    def save_input_resources(self) -> None:
        """Method run juste before the task run to save the input resource for this task.
          this will allow to know what resource this task uses as input
        """
        from .task_input_model import TaskInputModel
        for key, port in self.inputs.ports.items():

            resource_model: ResourceModel = port.resource_model

            # if the resource was already added for the task (for example multiple use in on Task)
            if resource_model is None:
                continue

            # Create the Input resource to save the resource use as input
            input_resource: TaskInputModel = TaskInputModel()
            input_resource.resource_model = resource_model
            input_resource.experiment = self.experiment
            input_resource.task_model = self

            parent = self.parent_protocol
            input_resource.protocol_model = parent
            input_resource.port_name = key
            input_resource.is_interface = parent.port_is_interface(key, port)

            input_resource.save()

    async def _run_task(self, task_runner: TaskRunner) -> None:
        """
        Run the task and save its state in the database.
        """

        try:
            # Run the task task
            await task_runner.run()

        except InvalidOutputsException as err:
            # Save the valid resources
            self._save_outputs(task_runner.get_outputs())
            raise err
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during task') from err

        # If success, save the outputs
        self._save_outputs(task_runner.get_outputs())

    def _save_outputs(self, task_outputs: TaskOutputs) -> None:
        for key, resource in task_outputs.items():

            if not self.outputs.port_exists(key):
                raise Exception(f"Error while saving the task output. The port '{key}' does not exists")

            resource_model: ResourceModel

            port: Port = self.outputs.get_port(key)

            if port.is_constant_out:
                # If the port is mark as unmodified, we don't create a new resource
                # We use the same resource
                resource_model = ResourceModel.get_by_id_and_check(resource._model_id)
            else:
                # create the resource model from the resource
                resource_model = ResourceModel.from_resource(resource)

                # Add info and save resource model
                resource_model.experiment = self.experiment
                resource_model.task_model = self
                resource_model.save_full()

            # save the resource model into the output's port (even if it's None)
            port.resource_model = resource_model

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
