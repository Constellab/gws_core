# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from typing import List, Type, final

from typing_extensions import TypedDict

from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_spec import InputSpec, IOSpec, IOSpecDict, OutputSpec


class PortDict(TypedDict):
    resource_id: str
    specs: IOSpecDict  # list of supported resource typing names


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    name: str

    _resource_model: ResourceModel = None
    _resource_spec: IOSpec = None

    # Switch to true when the set_resource_model is set (even if it is set with a None value)
    _resource_provided: bool = False

    def __init__(self, name: str, _resource_spec: IOSpec):
        self._resource_model = None
        self.name = name
        self._resource_spec = _resource_spec

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the port is ready (i.e. contains a resource), False otherwise.

        :return: True if the port is ready, False otherwise.
        :rtype: bool
        """

        # If the type is skippable, the port is always ready
        if self.is_optional:
            return True

        return self._resource_provided

    @property
    def is_optional(self) -> bool:
        """
        Returns True if the resource in this port is optional (optional or skippable), False otherwise

        :return: True if the resource is optional, False otherwise.
        :rtype: bool
        """

        return self.resource_spec.is_optional

    @property
    def is_empty(self) -> bool:
        return self._resource_model is None

    @property
    def is_constant_out(self) -> bool:
        """return true if the port type is ConstantOut

        :return: [description]
        :rtype: bool
        """
        return self.resource_spec.is_constant_out()

    @property
    def resource_provided(self) -> bool:
        """
        Returns True if the resource of the port was provided
        """

        return self._resource_provided

    def get_default_resource_type(self) -> Type[Resource]:
        return self.resource_spec.get_default_resource_type()

    def reset(self):
        self._resource_model = None
        self._resource_provided = False

    @property
    def resource_spec(self) -> IOSpec:
        """
        Returns the resource types of the port.

        :return: The resource
        :rtype: ResourceModel
        """

        return self._resource_spec

    @property
    def resource_model(self) -> ResourceModel:
        """
        Returns the resoruce of the port.

        :return: The resource
        :rtype: ResourceModel
        """

        return self._resource_model

    @resource_model.setter
    def resource_model(self, resource_model: ResourceModel) -> None:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """
        # mark the resource as provided
        self._resource_provided = True
        self._resource_model = resource_model

    def resource_type_is_compatible(self, resource_type: Type[Resource]) -> bool:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """

        if self.is_optional and resource_type is None:
            return True

        return self._resource_spec.is_compatible_with_resource_type(resource_type)

    def get_resource(self, new_instance: bool = False) -> Resource:
        return self.resource_model.get_resource(new_instance=new_instance)

    def to_json(self) -> PortDict:
        return {
            'resource_id': self.resource_model.id if self.resource_model else None,
            'specs': self.resource_spec.to_json()
        }

    def export_specs(self) -> IOSpecDict:
        return self.resource_spec.to_json()

    @classmethod
    def load_from_json(cls, json_: PortDict, name: str) -> 'Port':
        spec_type: Type[IOSpec] = cls._get_io_spec_type()
        specs: IOSpec = spec_type.from_json(json_['specs'])
        return cls(name, specs)

    @classmethod
    @abstractmethod
    def _get_io_spec_type(cls) -> Type[IOSpec]:
        pass


# ####################################################################
#
# InPort class
#
# ####################################################################
@final
class InPort(Port):
    """
    IntPort class representing input port
    """

    @classmethod
    def _get_io_spec_type(cls) -> Type[IOSpec]:
        return InputSpec


# ####################################################################
#
# OutPort class
#
# ####################################################################
@final
class OutPort(Port):
    """
    OutPort class representing output port
    """

    @classmethod
    def _get_io_spec_type(cls) -> Type[IOSpec]:
        return OutputSpec
