# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Generic, Type, TypeVar, final

from peewee import CharField, ModelSelect

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import typing_registrator
from ..model.viewable import Viewable
from ..resource.resource import Resource, SerializedResourceData
from .experiment_resource import ExperimentResource
from .processable_resource import ProcessableResource

if TYPE_CHECKING:
    from ..experiment.experiment import Experiment
    from ..processable.processable_model import ProcessableModel

# Typing names generated for the class Resource
CONST_RESOURCE_MODEL_TYPING_NAME = "GWS_CORE.gws_core.ResourceModel"

ResourceType = TypeVar('ResourceType', bound=Resource)


# Use the typing decorator to avoid circular dependency
@typing_registrator(unique_name="ResourceModel", object_type="GWS_CORE", hide=True)
class ResourceModel(Viewable, Generic[ResourceType]):
    """
    ResourceModel class.

    :property process: The process that created he resource
    :type process: ProcessableModel
    """
    # typing name of the resource model
    typing_name = CharField(null=False)

    # typing name of the resource
    resource_typing_name = CharField(null=False)

    # Path to the kv store if the kv exists for this resource model
    kv_store_path: CharField(null=True)

    _process: ProcessableModel = None
    _experiment: Experiment = None
    _table_name = 'gws_resource'
    _resource: ResourceType = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_MODEL_TYPING_NAME and type(self) != ResourceModel:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource model {self.full_classname()} is not decorated with @TypingDecorator, it can't be instantiate. Please decorate the class with @TypingDecorator")

        if self.typing_name is None:
            self.typing_name = self._typing_name
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
            resource_model_typing_name=self.typing_name,
        )
        mapping.save()
        self._experiment = experiment

    # -- P --

    @property
    def process(self) -> ProcessableModel:
        """
        Returns the parent process
        """

        if not self._process:
            try:
                processable_resource: ProcessableResource = ProcessableResource.get_by_id_and_tying_name(
                    self.id, self.typing_name)
                self._process = processable_resource.process
            except Exception as _:
                return None

        return self._process

    @process.setter
    def process(self, process: ProcessableModel):
        """
        Set the parent process
        """

        if self.process:
            return

        if not self.id:
            self.save()

        mapping = ProcessableResource(
            process_id=process.id,
            processable_typing_name=process.processable_typing_name,
            resource_model_id=self.id,
            resource_model_typing_name=self.typing_name,
        )
        mapping.save()
        self._process = process

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

    def _instantiate_resource(self, new_instance: bool = False) -> ResourceType:
        """
        Create the Resource object from the resource_typing_name
        """
        resource_type: Type[ResourceType] = TypingManager.get_type_from_name(self.resource_typing_name)

        data: dict
        if new_instance:
            data = copy.deepcopy(self.data)
        else:
            data = self.data
        # TODO handle KV STORE
        resource: ResourceType = resource_type()
        resource.deserialize_data(self.data)
        return resource

    # -- S --

    def delete_instance(self, *args, **kwargs):
        resource: ResourceType = self.get_resource()

        # TODO If there is a KVStore, delete it
        # if resource.data_is_kv_store():
        #     kv_store: KVStore = resource.data
        #     kv_store.remove()
        return super().delete_instance(*args, **kwargs)

    @classmethod
    def drop_table(cls, *args, **kwargs):
        """
        Drop model table
        """

        if not cls.table_exists():
            return

        super().drop_table(*args, **kwargs)
        ProcessableResource.drop_table()
        ExperimentResource.drop_table()

    @classmethod
    def from_resource(cls, resource: Resource) -> ResourceModel:
        """Create a new ResourceModel from a resource

        Don't set the resource here so it is regenerate on next get (avoid using same instance)

        :return: [description]
        :rtype: [type]
        """
        resource_model: ResourceModel = ResourceModel()
        resource_model.resource_typing_name = resource._typing_name
        resource_model._resource = resource

        serialized_data: SerializedResourceData = cls._serialize_resource_data(resource)

        # set the data
        resource_model.data = serialized_data

        # set the kv store
        # TODO handle KVStore
        # if resource_serialized.has_kv_store():
        #     resource_model.kv_store_path = resource_serialized.kv_store.file_path

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
                "process": {
                    "uri": self.process.uri,
                    "typing_name": self.process.processable_typing_name,
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
