# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Type, TypeVar, final

from peewee import CharField, ModelSelect

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
from ..model.viewable import Viewable
from ..resource.resource import Resource
from .experiment_resource import ExperimentResource
from .kv_store import KVStore
from .processable_resource import ProcessableResource

if TYPE_CHECKING:
    from ..experiment.experiment import Experiment
    from ..processable.processable_model import ProcessableModel

# Typing names generated for the class Resource
CONST_RESOURCE_MODEL_TYPING_NAME = "GWS_CORE.gws_core.ResourceModel"

ResourceType = TypeVar('ResourceType', bound=Resource)


# Use the typing decorator to avoid circular dependency
@TypingDecorator(unique_name="ResourceModel", object_type="GWS_CORE", hide=True)
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
    def get_resource(self) -> ResourceType:
        """
        Returns the resource created from the data and resource_typing_name
        """
        if self._resource is None:
            self._resource = self._instantiate_resource()

        return self._resource

    def _instantiate_resource(self) -> ResourceType:
        """
        Create the Resource object from the resource_typing_name
        """
        resource_type: Type[ResourceType] = TypingManager.get_type_from_name(self.resource_typing_name)
        return resource_type(data=self.data)

    # -- S --

    def delete_instance(self, *args, **kwargs):
        resource: ResourceType = self.get_resource()
        if resource.data_is_kv_store():
            kv_store: KVStore = resource.data
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
        ProcessableResource.drop_table()
        ExperimentResource.drop_table()

    @classmethod
    def from_resource(cls, resource: Resource) -> ResourceModel:
        """Create a new ResourceModel from a resource

        :return: [description]
        :rtype: [type]
        """
        resource_model: ResourceModel = ResourceModel()
        resource_model.resource_typing_name = resource._typing_name
        resource_model._resource = resource  # set the resource into the resource model
        resource_model.data = resource.to_json()  # set the data
        return resource_model

    # -- K --

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
