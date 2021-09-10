# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Generic, Optional, Type, TypeVar, final

from peewee import CharField, ModelSelect

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import typing_registrator
from ..model.viewable import Viewable
from ..resource.kv_store import KVStore
from ..resource.resource import Resource, SerializedResourceData
from .experiment_resource import ExperimentResource
from .task_resource import TaskResource

if TYPE_CHECKING:
    from ..experiment.experiment import Experiment
    from ..task.task_model import TaskModel

# Typing names generated for the class Resource
CONST_RESOURCE_MODEL_TYPING_NAME = "GWS_CORE.gws_core.ResourceModel"

ResourceType = TypeVar('ResourceType', bound=Resource)

# Use the typing decorator to avoid circular dependency


@typing_registrator(unique_name="ResourceModel", object_type="GWS_CORE", hide=True)
class ResourceModel(Viewable, Generic[ResourceType]):
    """
    ResourceModel class.
    """

    # typing name of the resource
    resource_typing_name = CharField(null=False)

    # Path to the kv store if the kv exists for this resource model
    kv_store_path = CharField(null=True)

    _task_model: TaskModel = None
    _experiment: Experiment = None
    _table_name = 'gws_resource'
    _resource: ResourceType = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_MODEL_TYPING_NAME and type(self) != ResourceModel:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource model {self.full_classname()} is not decorated with @TypingDecorator, it can't be instantiate. Please decorate the class with @TypingDecorator")

    # -- E --

    @property
    def experiment(self):
        """
        Returns the parent experiment
        """

        if not self._experiment:
            try:
                mapping: ExperimentResource = ExperimentResource.get_by_id_and_tying_name(
                    self.id, self.resource_typing_name)
                self._experiment = mapping.experiment
            except:
                return None

        return self._experiment

    @experiment.setter
    def experiment(self, experiment: Experiment):
        """
        Set the parent experiment
        """

        if self.experiment:
            return

        if not self.id:
            self.save()

        mapping = ExperimentResource(
            experiment_id=experiment.id,
            resource_model_id=self.id,
            resource_model_typing_name=self._typing_name,
        )
        mapping.save()
        self._experiment = experiment

    # -- P --

    @property
    def task(self) -> TaskModel:
        """
        Returns the parent task model
        """

        if not self._task_model:
            try:
                task_resource: TaskResource = TaskResource.get_by_id_and_tying_name(
                    self.id, self._typing_name)
                self._task_model = task_resource.task_model
            except Exception as _:
                return None

        return self._task_model

    @task.setter
    def task(self, task: TaskModel):
        """
        Set the parent task
        """

        if self.task:
            return

        if not self.id:
            self.save()

        mapping = TaskResource(
            task_model_id=task.id,
            resource_model_id=self.id,
            resource_model_typing_name=self._typing_name,
        )
        mapping.save()
        self._task_model = task

    @property
    def typing_name(self) -> str:
        return self._typing_name

    # -- R --
    @final
    def get_resource(self, new_instance: bool = False) -> ResourceType:
        """
        Returns the resource created from the data and resource_typing_name
        if new_instance, it forces to rebuild the resource
        """

        if new_instance:
            return self._instantiate_resource(new_instance=new_instance)

        if self._resource is None:
            self._resource = self._instantiate_resource(new_instance=new_instance)

        return self._resource

    @final
    def get_kv_store(self) -> Optional[KVStore]:
        if not self.kv_store_path:
            return None

        # Create the KVStore from the path
        kv_store: KVStore = KVStore(self.kv_store_path)

        # Lock the kvstore so the file can't be updated
        kv_store.lock(KVStore.get_full_file_path(file_name=self.uri, with_extension=False))
        return kv_store

    @final
    def get_kv_store_with_default(self) -> KVStore:
        """Get the KVStore and create an empty one if it doesn't exist

        :return: [description]
        :rtype: KVStore
        """
        kv_store: Optional[KVStore] = self.get_kv_store()
        if kv_store:
            return kv_store
        # if there is a default kv store to return
        return KVStore.from_filename(self.uri)

    def _instantiate_resource(self, new_instance: bool = False) -> ResourceType:
        """
        Create the Resource object from the resource_typing_name
        """
        resource_type: Type[ResourceType] = TypingManager.get_type_from_name(self.resource_typing_name)
        resource: ResourceType = resource_type(binary_store=self.get_kv_store_with_default())
        # Pass the model uri to the resource
        resource._model_uri = self.uri

        self.send_fields_to_resource(resource, new_instance)  # synchronize the resource fields with the model fields
        return resource

    def send_fields_to_resource(self, resource: Resource, new_instance: bool):
        data: dict
        if new_instance:
            data = copy.deepcopy(self.data)
        else:
            data = self.data
        resource.deserialize_data(data)

    def receive_fields_from_resource(self, resource):
        serialized_data: SerializedResourceData = self._serialize_resource_data(resource)
        self.data = serialized_data

    def delete_instance(self, *args, **kwargs):
        kv_store: Optional[KVStore] = self.get_kv_store()
        if kv_store:
            kv_store.remove()
        return super().delete_instance(*args, **kwargs)

    @classmethod
    def drop_table(cls, *args, **kwargs):
        """
        Drop model table
        """

        if not cls.table_exists():
            return

        super().drop_table(*args, **kwargs)
        TaskResource.drop_table()
        ExperimentResource.drop_table()

    @classmethod
    def from_resource(cls, resource: Resource) -> ResourceModel:
        """Create a new ResourceModel from a resource

        Don't set the resource here so it is regenerate on next get (avoid using same instance)

        :return: [description]
        :rtype: [type]
        """
        resource_model_type = resource.get_resource_model_type()
        resource_model: ResourceModel = resource_model_type()
        resource_model.resource_typing_name = resource._typing_name

        # synchronize the model fields with the resource fields
        resource_model.receive_fields_from_resource(resource)

        # set the kv store
        kv_store: KVStore = resource.binary_store
        if kv_store is not None:
            if not isinstance(kv_store, KVStore):
                raise BadRequestException(
                    f"The binary_store property of the resource {resource.full_classname()} is not an instance of KVStore")

            # If the kv store file exists (this mean that we wrote on it)
            if kv_store.file_exists():
                # Save the kv store path on the resource
                resource_model.kv_store_path = kv_store.get_full_path_without_extension()
            else:
                resource_model.kv_store_path = None
        else:
            resource_model.kv_store_path = None

        return resource_model

    # -- K --
    @classmethod
    def _serialize_resource_data(cls, resource: Resource) -> SerializedResourceData:
        """Serialize a resource, check result and return serialized resource
        """
        serialized_data: SerializedResourceData = resource.serialize_data()

        if serialized_data is None:
            return None

        if not isinstance(serialized_data, dict):
            raise BadRequestException(
                f"The serialisation_data method of resource '{resource.full_classname()}' did not return a Dictionary but a {type(serialized_data)}. It must return a 'ResourceSerialized' object.")

        return serialized_data

    @classmethod
    def select_me(cls, *args, **kwargs) -> ModelSelect:
        """
        Select objects by ensuring that the object-type is the same as the current model.
        """

        return cls.select(*args, **kwargs).where(cls.resource_typing_name == cls._typing_name)

    # -- T --
    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)
        if self.experiment:
            _json.update({
                "experiment": {"uri": self.experiment.uri},
                "task": {
                    "uri": self.task.uri,
                    "typing_name": self.task.processable_typing_name,
                },
            })

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model data.
        :return: The representation
        :rtype: `dict`
        """

        if deep:
            return self.get_resource().to_json()
        else:
            return {}

    # -- V --
