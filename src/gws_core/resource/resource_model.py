# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

import copy
from typing import (TYPE_CHECKING, Any, Dict, Generic, Optional, Type, TypeVar,
                    final)

from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file_r_field import FileRField
from gws_core.resource.r_field import BaseRField
from peewee import CharField

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import typing_registrator
from ..model.viewable import Viewable
from ..resource.kv_store import KVStore
from ..resource.resource import Resource
from .experiment_resource import ExperimentResource
from .task_resource import TaskResource

if TYPE_CHECKING:
    from ..experiment.experiment import Experiment
    from ..task.task_model import TaskModel

# Typing names generated for the class Resource
CONST_RESOURCE_MODEL_TYPING_NAME = "MODEL.gws_core.ResourceModel"

ResourceType = TypeVar('ResourceType', bound=Resource)

# Use the typing decorator to avoid circular dependency


@typing_registrator(unique_name="ResourceModel", object_type="MODEL", hide=True)
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

    ########################################## MODEL METHODS ######################################

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

    ########################################## RESOURCE ######################################
    @final
    def get_resource(self, new_instance: bool = False) -> ResourceType:
        """
        Returns the resource created from the data and resource_typing_name
        if new_instance, it forces to rebuild the resource
        """

        if new_instance:
            return self._instantiate_resource()

        if self._resource is None:
            self._resource = self._instantiate_resource()

        return self._resource

    def _instantiate_resource(self) -> ResourceType:
        """
        Create the Resource object from the resource_typing_name
        """
        resource_type: Type[ResourceType] = self._get_resource_type()
        resource: ResourceType = resource_type()
        # Pass the model uri to the resource
        resource._model_uri = self.uri

        self.send_fields_to_resource(resource)
        return resource

    @classmethod
    def from_resource(cls, resource: ResourceType) -> ResourceModel:
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

        return resource_model

    def send_fields_to_resource(self, resource: ResourceType):
        """for each BaseRField of the resource, set the value form the data or kvstore

        :param resource: [description]
        :type resource: ResourceType
        """
        properties: Dict[str, BaseRField] = self._get_resource_r_fields(type(resource))

        kv_store: KVStore = self.get_kv_store()

        # for each BaseRField of the resource, set the value form the data or kvstore
        for key, r_field in properties.items():

            loaded_value: Any = None
            # If the property is searchable, it is stored in the DB
            if r_field.searchable:
                loaded_value = copy.deepcopy(r_field.deserialize(self.data.get(key)))

            elif kv_store is not None:
                loaded_value = r_field.deserialize(kv_store.get(key))

            setattr(resource, key, loaded_value)

    def receive_fields_from_resource(self, resource: ResourceType):
        """for each BaseRField of the resource, store its value to the data or kvstore

        :param resource: [description]
        :type resource: ResourceType
        """
        self.data = {}
        # init the kvstore, the directory is not created until we write on the kvstore
        kv_store: KVStore = self._get_or_create_kv_store()

        # get the r_fields of the resource
        r_fields: Dict[str, BaseRField] = self._get_resource_r_fields(type(resource))

        for key, r_field in r_fields.items():
            # get the attribute value corresponding to the r_field
            r_field_value: Any = getattr(resource, key)

            # specific case for the FileRField
            if isinstance(r_field, FileRField):
                # generate a new file path inside the kv store directory
                file_path = kv_store.generate_new_file()

                # dump the resource value into the file
                r_field.dump_to_file(r_field_value, str(file_path))
                # store the file path in the kv_store
                kv_store[key] = file_path
                continue

            value: Any = r_field.serialize(r_field_value)
            # If the property is searchable, store it in the DB
            if r_field.searchable:
                self.data[key] = value

            # Otherwise, store it in the kvstore
            else:
                kv_store[key] = value

    def _get_resource_r_fields(self, resource_type: Type[ResourceType]) -> Dict[str, BaseRField]:
        """Get the list of resource's r_fields,
        the key is the property name, the value is the BaseRField object
        """
        return Utils.get_property_names_of_type(resource_type, BaseRField)

    def _get_resource_type(self) -> Type[ResourceType]:
        return TypingManager.get_type_from_name(self.resource_typing_name)

    ########################################## KV STORE ######################################

    @final
    def get_kv_store(self) -> Optional[KVStore]:
        if not self.kv_store_path:
            return None

        # Create the KVStore from the path
        kv_store: KVStore = KVStore(self.kv_store_path)

        # Lock the kvstore so the file can't be updated
        kv_store.lock(KVStore.get_full_file_path(file_name=self.uri, with_extension=False))
        return kv_store

    def _get_or_create_kv_store(self) -> KVStore:
        """Get the KVStore and create an empty one if it doesn't exist

        :return: [description]
        :rtype: KVStore
        """
        kv_store: Optional[KVStore] = self.get_kv_store()
        if kv_store:
            return kv_store

        # Create the KV store
        kv_store = KVStore.from_filename(self.uri)

        self.kv_store_path = kv_store.get_full_path_without_extension()
        return kv_store

    ########################################## JSON ######################################

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

        _json["typing_name"] = self._typing_name
        if self.experiment:
            _json.update({
                "experiment": {"uri": self.experiment.uri},
                "task": {
                    "uri": self.task.uri,
                    "typing_name": self.task.process_typing_name,
                },
            })

        resource: ResourceType = self.get_resource()
        _json["resource_human_name"] = resource._human_name
        _json["resource_short_description"] = resource._short_description

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model data.
        :return: The representation
        :rtype: `dict`
        """

        if deep:
            return self.get_resource().view_as_dict()
        else:
            return {}
