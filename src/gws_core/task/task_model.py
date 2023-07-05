# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import inspect
import zlib
from typing import Any, Dict, List, Type

from peewee import ForeignKeyField, ModelSelect

from gws_core.core.utils.date_helper import DateHelper
from gws_core.resource.resource_set.resource_list_base import ResourceListBase

from ..config.config_types import ConfigParamsDict
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.utils.logger import Logger
from ..core.utils.reflector_helper import ReflectorHelper
from ..io.io import Inputs, Outputs
from ..io.io_exception import InvalidOutputsException
from ..io.port import Port
from ..model.typing_manager import TypingManager
from ..process.process_exception import (CheckBeforeTaskStopException,
                                         ProcessRunException)
from ..process.process_model import ProcessModel, ProcessStatus
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel, ResourceOrigin
from ..resource.resource_r_field import ResourceRField
from ..task.task_io import TaskOutputs
from .task import CheckBeforeTaskResult, Task
from .task_runner import TaskRunner


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

    # Only for task of type Source, this is to store the resource used in config
    # with lazy load = false, the Resource is not Loaded, it only contains the id
    source_config_id: str = ForeignKeyField(
        ResourceModel, null=True, index=True, lazy_load=False)

    _table_name = 'gws_task'

    def create_source_zip(self):
        """
        Returns the zipped code source of the task
        """

        # /:\ Use the true object type (self.type)
        model_t: Type[TaskModel] = TypingManager.get_type_from_name(
            self.process_typing_name)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())

    def set_process_type(self, typing_name: str) -> None:
        """Method used when creating a new task model, it init the input and output from task specs
        """
        super().set_process_type(typing_name)

        task_type: Type[Task] = self.get_process_type()

        self._inputs = Inputs(task_type.input_specs.is_dynamic())
        # create the input ports from the Task input specs
        for k in task_type.input_specs.get_specs():
            self._inputs.create_port(k, task_type.input_specs.get_spec(k))

        # Set the data inputs dict
        self.data["inputs"] = self.inputs.to_json()

        self._outputs = Outputs(task_type.input_specs.is_dynamic())
        # create the output ports from the Task output specs
        for k in task_type.output_specs.get_specs():
            self._outputs.create_port(k, task_type.output_specs.get_spec(k))

        # Set the data inputs dict
        self.data["outputs"] = self.outputs.to_json()

    def _create_task_instance(self) -> Task:
        return self.get_process_type()()

    def is_protocol(self) -> bool:
        return False
    ################################# MODEL METHODS #############################

    def save_full(self) -> 'TaskModel':
        self.config.save()
        self.progress_bar.save()
        return self.save()

    @transaction()
    def archive(self, archive: bool) -> 'TaskModel':
        """
        Archive the process
        """

        if self.is_archived == archive:
            return self

        super().archive(archive)

        # -> try to archive the config if possible!
        self.config.archive(archive)
        for resource in self.resources:
            resource.archive(archive)

        return self

    @property
    def resources(self) -> List[ResourceModel]:
        if not self.is_saved():
            return []

        return list(ResourceModel.select().where(ResourceModel.task_model == self))

    @classmethod
    def get_source_task_using_resource_in_another_experiment(
            cls, resource_model_ids: List[str], exclude_experimence_id: str) -> ModelSelect:
        """
        Returns the source task models configured with one of the provided resource that are not the the provided experiment
        """

        return cls.select().where(
            (cls.source_config_id.in_(resource_model_ids)) &
            (cls.experiment != exclude_experimence_id)
        )

    ################################# RUN #############################

    def _run(self) -> None:
        """
        Run the task and save its state in the database.
        """

        # build the task tester
        params: ConfigParamsDict = self.config.get_values()
        inputs: Dict[str, Resource] = self.inputs.get_resources(new_instance=True)

        task_runner: TaskRunner = TaskRunner(
            task_type=self.get_process_type(),
            params=params,
            inputs=inputs,
            config_model_id=self.config.id,
            input_specs=self.inputs.get_specs(),
            output_specs=self.outputs.get_specs())
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
            raise CheckBeforeTaskStopException(
                message=check_result.get('message'))

        self._run_before_task()

        # run the task
        self._run_task(task_runner)

        # execute the run after task method
        try:
            task_runner.run_after_task()
        except Exception as err:
            if not isinstance(err, ProcessRunException):
                Logger.log_exception_stack_trace(err)
            raise ProcessRunException.from_exception(process_model=self, exception=err,
                                                     error_prefix='Error during check after task') from err

        self._run_after_task()

    def _run_before_task(self) -> None:
        super()._run_before_task()

        # Store all the resources user as input for this taks
        self.save_input_resources()

    def save_input_resources(self) -> None:
        """Method run just before the task run to save the input resource for this task.
          this will allow to know what resource this task uses as input
        """
        from .task_input_model import TaskInputModel
        for key, port in self.inputs.ports.items():

            resource_model: ResourceModel = port.resource_model

            if resource_model is None:
                continue

            if not resource_model.is_saved():
                raise Exception(
                    f"The resource of port '{key}' is not saved, it can't be used as input of the task")

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

    def _run_task(self, task_runner: TaskRunner) -> None:
        """
        Run the task and save its state in the database.
        """

        try:
            # Run the task task
            task_runner.run()

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
                raise Exception(
                    f"Error while saving the task output. The port '{key}' does not exists")

            resource_model: ResourceModel

            port: Port = self.outputs.get_port(key)

            if port.is_constant_out:
                # If the port is mark as is_constant_out, we don't create a new resource
                # We use the same resource
                resource_model = ResourceModel.get_by_id_and_check(
                    resource._model_id)
            else:
                resource_model = self._save_resource(resource, port.name)

            # save the resource model into the output's port (even if it's None)
            port.resource_model = resource_model

    def _save_resource(self, resource: Resource, port_name: str) -> ResourceModel:
        """Save the resource
        """

        # Handle specific case of ResourceSet, it saves all the sub
        new_children_resources: List[ResourceModel] = []
        if isinstance(resource, ResourceListBase):
            new_children_resources = self._save_resource_list(
                resource, port_name)

        # check the resource r field before saving
        self._check_resource_r_fields(resource, port_name)

        # create and save the resource model from the resource
        resource_model = ResourceModel.save_from_resource(
            resource, origin=ResourceOrigin.GENERATED, experiment=self.experiment, task_model=self, port_name=port_name)

        # update the parent of new children resource
        if isinstance(resource, ResourceListBase):
            for child_resource in new_children_resources:
                child_resource.parent_resource_id = resource_model.id
                child_resource.save()

        return resource_model

    def _save_resource_list(self, resource_list: ResourceListBase, port_name: str) -> List[ResourceModel]:
        """Specific management to save resources of a resource set, return the new created resources
        """

        new_children_resources: List[ResourceModel] = []
        for resource in resource_list.get_resources_as_set():

            # if this is a new resource
            if not resource_list.__resource_is_constant__(resource.uid):

                # create and save the resource model from the resource
                resource_model = self._save_resource(resource, port_name)

                resource._model_id = resource_model.id
                new_children_resources.append(resource_model)
            else:
                # case when the resource is a constant and we don't create a new resource
                # if the resource is not listed in task input, error
                if not self.inputs.has_resource_model(resource._model_id):
                    raise BadRequestException(GWSException.INVALID_LINKED_RESOURCE.value,
                                              unique_code=GWSException.INVALID_LINKED_RESOURCE.name,
                                              detail_args={'port_name': port_name})

        resource_list._set_r_field()
        return new_children_resources

    def _check_resource_r_fields(self, resource: Resource, port_name: str):
        """check all ResourceRField are resource that are input of the task
        """

        # get the ResourceRField of the resource
        r_fields: Dict[str, ResourceRField] = ReflectorHelper.get_property_names_of_type(
            type(resource), ResourceRField)

        for key, r_field in r_fields.items():
            # get the attribute value corresponding to the r_field
            r_field_value: Any = getattr(resource, key)

            # retrieve the resource model id
            resource_model_id = r_field.serialize(r_field_value)

            if not resource_model_id:
                continue

            # if the resource r field is not listed in task input, error
            if not self.inputs.has_resource_model(resource_model_id):
                raise BadRequestException(GWSException.INVALID_LINKED_RESOURCE.value,
                                          unique_code=GWSException.INVALID_LINKED_RESOURCE.name,

                                          detail_args={'port_name': port_name})

    def mark_as_started(self):
        if self.is_running:
            return
        self.progress_bar.start()
        self.progress_bar.add_message(
            f"Start of task '{self.get_instance_name_context()}'")
        self.status = ProcessStatus.RUNNING
        self.started_at = DateHelper.now_utc()
        self.save()

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
