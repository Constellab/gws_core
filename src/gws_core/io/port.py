from abc import abstractmethod
from typing import TypeVar, final

from gws_core.io.io_dto import PortDTO

from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_spec import InputSpec, IOSpec, IOSpecDTO, OutputSpec

# For generic Port type
PortType = TypeVar("PortType", bound="Port")


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    name: str

    _resource_id: str | None = None
    _spec: IOSpecDTO = None

    # use to cache the resource model
    _resource_model: ResourceModel = None
    # use to cache the resource spec
    _resource_spec: IOSpec = None

    # Switch to true when the set_resource_model is set (even if it is set with a None value)
    _resource_provided: bool = False

    def __init__(self, name: str, spec: IOSpecDTO) -> None:
        self._resource_id = None
        self._resource_model = None
        self.name = name
        self._spec = spec

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the port is ready (i.e. contains a resource), False otherwise.

        :return: True if the port is ready, False otherwise.
        :rtype: bool
        """

        # If the type is skippable, the port is always ready
        if self.optional:
            return True

        return self._resource_provided

    @property
    def optional(self) -> bool:
        """
        Returns True if the resource in this port is optional (optional or skippable), False otherwise

        :return: True if the resource is optional, False otherwise.
        :rtype: bool
        """

        return self.resource_spec.optional

    @property
    def is_empty(self) -> bool:
        return self._resource_id is None

    @property
    def constant_out(self) -> bool:
        """return true if the port type is ConstantOut

        :return: [description]
        :rtype: bool
        """
        return self.resource_spec.constant_out()

    @property
    def resource_provided(self) -> bool:
        """
        Returns True if the resource of the port was provided
        """

        return self._resource_provided

    def get_default_resource_type(self) -> type[Resource]:
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
        if not self._resource_spec:
            spec_type: type[IOSpec] = self._get_io_spec_type()
            try:
                self._resource_spec = spec_type.from_dto(self._spec)
            except Exception as e:
                raise ValueError(
                    f"{self._get_type_name()} port '{self.get_human_name()}' ({self.name}) has invalid resource spec. {e}"
                )

        return self._resource_spec

    def get_resource_model(self) -> ResourceModel | None:
        if self._resource_model is None and self._resource_id is not None:
            self._resource_model = ResourceModel.get_by_id(self._resource_id)
        return self._resource_model

    def set_resource_model(self, resource_model: ResourceModel | None) -> None:
        self._resource_model = resource_model
        self._resource_id = resource_model.id if resource_model else None
        self._resource_provided = True

    def set_resource_model_id(self, resource_id: str | None) -> None:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """
        # mark the resource as provided
        self._resource_id = resource_id
        self._resource_model = None
        self._resource_provided = True

    def get_resource_model_id(self) -> str | None:
        return self._resource_id

    def resource_type_is_compatible(self, resource_type: type[Resource]) -> bool:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """

        if self.optional and resource_type is None:
            return True

        return self.resource_spec.is_compatible_with_resource_type(resource_type)

    def get_resource(self, new_instance: bool = False) -> Resource:
        if self.is_empty:
            return None
        return self.get_resource_model().get_resource(new_instance=new_instance)

    def get_human_name(self) -> str:
        return self._spec.human_name or self.name

    def to_dto(self) -> PortDTO:
        return PortDTO(resource_id=self._resource_id, specs=self._spec)

    @classmethod
    def load_from_dto(cls: type[PortType], dto: PortDTO, name: str) -> PortType:
        port: PortType = cls(name, dto.specs)

        if dto.resource_id:
            port.set_resource_model_id(dto.resource_id)

        return port

    @classmethod
    @abstractmethod
    def _get_io_spec_type(cls) -> type[IOSpec]:
        pass

    @classmethod
    @abstractmethod
    def _get_type_name(cls) -> str:
        pass


@final
class InPort(Port):
    """
    IntPort class representing input port
    """

    @classmethod
    def _get_io_spec_type(cls) -> type[IOSpec]:
        return InputSpec

    @classmethod
    def _get_type_name(cls) -> str:
        return "Input"


@final
class OutPort(Port):
    """
    OutPort class representing output port
    """

    @classmethod
    def _get_io_spec_type(cls) -> type[IOSpec]:
        return OutputSpec

    @classmethod
    def _get_type_name(cls) -> str:
        return "Output"
