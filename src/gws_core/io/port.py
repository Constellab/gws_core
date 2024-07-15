

from abc import abstractmethod
from typing import Optional, Type, TypeVar, final

from gws_core.io.io_dto import PortDTO

from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_spec import InputSpec, IOSpec, OutputSpec

# For generic Port type
PortType = TypeVar('PortType', bound='Port')


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    name: str

    _resource_id: Optional[str] = None
    # use to cache the resource model
    _resource_model: ResourceModel = None
    _resource_spec: IOSpec = None

    # Switch to true when the set_resource_model is set (even if it is set with a None value)
    _resource_provided: bool = False

    def __init__(self, name: str, _resource_spec: IOSpec):
        self._resource_id = None
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
        return self._resource_id is None

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
        self._resource_id = None
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

    def get_resource_model(self) -> Optional[ResourceModel]:
        if self._resource_model is None and self._resource_id is not None:
            self._resource_model = ResourceModel.get_by_id(self._resource_id)
        return self._resource_model

    def set_resource_model(self, resource_model: Optional[ResourceModel]) -> None:
        self._resource_model = resource_model
        self._resource_id = resource_model.id if resource_model else None
        self._resource_provided = True

    def set_resource_model_id(self, resource_id: Optional[str]) -> None:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """
        # mark the resource as provided
        self._resource_id = resource_id
        self._resource_model = None
        self._resource_provided = True

    def get_resource_model_id(self) -> Optional[str]:
        return self._resource_id

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
        if self.is_empty:
            return None
        return self.get_resource_model().get_resource(new_instance=new_instance)

    def to_dto(self) -> PortDTO:
        return PortDTO(
            resource_id=self._resource_id,
            specs=self.resource_spec.to_dto()
        )

    @classmethod
    def load_from_dto(cls: Type[PortType], dto: PortDTO, name: str) -> PortType:
        spec_type: Type[IOSpec] = cls._get_io_spec_type()
        specs: IOSpec = spec_type.from_dto(dto.specs)
        return cls(name, specs)

    @classmethod
    @abstractmethod
    def _get_io_spec_type(cls) -> Type[IOSpec]:
        pass


@final
class InPort(Port):
    """
    IntPort class representing input port
    """

    @classmethod
    def _get_io_spec_type(cls) -> Type[IOSpec]:
        return InputSpec


@final
class OutPort(Port):
    """
    OutPort class representing output port
    """

    @classmethod
    def _get_io_spec_type(cls) -> Type[IOSpec]:
        return OutputSpec
