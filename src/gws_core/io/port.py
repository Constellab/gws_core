
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, List, Tuple, Type, final

from ..core.exception.exceptions import BadRequestException
from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_types import IOSpec, PortDict

if TYPE_CHECKING:
    from ..processable.processable_model import ProcessableModel
    from .connector import Connector
    from .io import IO


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    _resource_model: ResourceModel = None
    _resource_types: List[Type[Resource]] = None
    _prev: 'Port' = None
    _next: List['Port'] = []
    _parent: IO

    def __init__(self, parent: IO, resource_types: IOSpec):
        self._resource_model = None
        self._prev = None
        self._next = []
        self._parent = parent

        self.set_resource_types(resource_types)

    # -- D --

    def disconnect(self):
        """
        Disconnect the port
        """

        if self._prev:
            self._prev._next = []

        for port in self._next:
            port._prev = None

        self._prev = None
        self._next = []

    # -- G --

    def get_default_resource_type(self):
        return self.resource_types[0]

    # -- I --

    @property
    def is_connected(self) -> bool:
        """
        Returns True if the port is left-connected or right-connected to a another port.

        :return: True if the port is left-connected or right-connected, False otherwise.
        :rtype: bool
        """

        return self.is_left_connected or self.is_right_connected

    @property
    def is_left_connected(self) -> bool:
        """
        Returns True if the port is left-connected to a another port.

        :return: True if the port is left-connected, False otherwise.
        :rtype: bool
        """
        return not self._prev is None

    def is_left_connected_to(self, port: 'Port') -> bool:
        """
        Returns True if the port is left-connected to a given Port, False otherwise.

        :return: True if the port is connected, False otherwise.
        :rtype: bool
        """
        return self._prev is port

    @property
    def is_right_connected(self) -> bool:
        """
        Returns True if the port is right-connected to a another port.

        :return: True if the port is right-connected, False otherwise.
        :rtype: bool
        """
        return len(self._next) > 0

    def is_right_connected_to(self, port: 'Port') -> bool:
        """
        Returns True if the port is right-connected to a given Port, False otherwise.

        :return: True if the port is connected, False otherwise.
        :rtype: bool
        """
        return port in self._next

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the port is ready (i.e. contains a resource), False otherwise.

        :return: True if the port is ready, False otherwise.
        :rtype: bool
        """

        if self.is_optional:
            return True

        # if self._resource is None:
        #    return self.is_optional and (not self.is_connected)

        # and self._resource.is_saved()
        return self.resource_model is not None

    @property
    def is_optional(self) -> bool:
        """
        Returns True if the resource in this port is optional, False otherwise

        :return: True if the resource is optional, False otherwise.
        :rtype: bool
        """

        return None in self.resource_types

    @property
    def is_empty(self) -> bool:
        return self._resource_model is None

    # -- G --

    def get_next_procs(self) -> List[ProcessableModel]:
        """
        Returns the list of right-hand side processes connected to the port.

        :return: List of processes
        :rtype: list
        """
        next_proc = []
        for port in self._next:
            io = port._parent
            next_proc.append(io._parent)
        return next_proc

    # -- N --

    @property
    def next(self) -> List['Port']:
        return self._next

    # -- P --

    @property
    def prev(self) -> 'Port':
        return self._prev

    @property
    def parent(self) -> IO:
        """
        Returns the parent IO of the Port, i.e. the IO (Input or Output) that holds this Port.

        :return: The parent IO
        :rtype: IO
        """
        return self._parent

    @property
    def process(self) -> ProcessableModel:
        """
        Returns the parent Process of the Port.

        :return: The parent Process
        :rtype: Process
        """

        return self.parent.parent

    def propagate(self):
        """
        Propagates the resource of the port to the connected (right-hande side) port
        """

        for port in self._next:
            port.resource_model = self._resource_model

    def __or__(self, other: 'Port'):
        raise BadRequestException(
            "Port cannot be . Use InPort or OutPort class")

    # -- R --

    def reset(self):
        self._resource_model = None
        # for port in self._next:
        #    port._resource = None

    @property
    def resource_types(self) -> List[Type[Resource]]:
        """
        Returns the resource types of the port.

        :return: The resource
        :rtype: ResourceModel
        """

        return self._resource_types

    def get_resource_typing_names(self) -> List[str]:
        specs: List[str] = []
        for resource_type in self.resource_types:
            if resource_type is None:
                specs.append(None)
            else:
                specs.append(resource_type._typing_name)
        return specs

    # -- S --
    def set_resource_types(self, resource_types: IOSpec):
        """
        Sets the resource_types of the port.

        :param resource: The input resource
        :type resource: Resource
        """

        # if the type is a Union or Optional (equivalient to Union[x, None])
        if hasattr(resource_types, "__args__") and isinstance(resource_types.__args__, tuple):
            resource_types = resource_types.__args__
        elif not isinstance(resource_types, Iterable):
            resource_types = [resource_types]

        checked_type: List[Type[Resource], None] = []

        for res_t in resource_types:
            # convert the NoneType to None
            if res_t is type(None):
                checked_type.append(None)
                continue

            # check that the type is a resource Resource
            if res_t is not None and not issubclass(res_t, Resource):
                raise BadRequestException(
                    "Invalid port specs. The resources types must refer to a subclass of Resource")
            checked_type.append(res_t)

        self._resource_types = checked_type

    @property
    def resource_model(self) -> ResourceModel:
        """
        Returns the resoruce of the port.

        :return: The resource
        :rtype: ResourceModel
        """

        return self._resource_model

    # -- S --
    @resource_model.setter
    def resource_model(self, resource: Resource) -> None:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """

        if self.is_optional and resource is None:
            return

        self._resource_model = resource

    # -- S --
    def resource_type_is_compatible(self, resource_type: Type[Resource]) -> bool:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """

        if self.is_optional and resource_type is None:
            return True

        # check that the resource type is is subclass of one of the port resources types
        for accepted_type in self._resource_types:
            if accepted_type is None:
                continue

            if issubclass(resource_type, accepted_type):
                return True

        return False

    def get_resource(self) -> Resource:
        return self.resource_model.get_resource()

    @property
    def name(self) -> str:
        """overiden by the children

        """
        pass

    def to_json(self) -> PortDict:
        _json = {}

        if self.resource_model:
            _json["resource"] = {
                "uri": self.resource_model.uri,
                "typing_name": self.resource_model.typing_name
            }
        else:
            _json["resource"] = {
                "uri": "",
                "typing_name": ""
            }

        _json["specs"] = self.get_resource_typing_names()

        return _json


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

    # -- N --

    @property
    def name(self) -> str:
        """
        Returns the name of the port.

        :return: The name
        :rtype: str
        """

        proc = self.parent.parent
        proc_input = proc.input
        for name in proc_input._ports:
            if proc_input._ports[name] is self:
                return name
        return None

    def __or__(self, other: 'Port'):
        raise BadRequestException(
            "The input port cannot be connected on the right")


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

    def _are_compatible_types(self, other: 'InPort') -> bool:
        for left_type in self.resource_types:
            if other.resource_type_is_compatible(left_type):
                return True

        return False

    def pipe(self, other: 'InPort', lazy: bool = False) -> Connector:
        """
        Connection operator.

        Connect the output port to another (right-hand side) input port.
        :return: The right-hand sode port
        :rtype: Port
        """

        if not isinstance(other, InPort):
            raise BadRequestException(
                "The output port can only be connected to an input port")

        if other.is_left_connected:
            raise BadRequestException(
                "The right-hand side port is already connected")

        if self == other:
            raise BadRequestException("Self connection not allowed")

        if not lazy:
            # hard checking of port compatibility
            if not self._are_compatible_types(other):
                raise BadRequestException(
                    f"Invalid connection. {self.resource_types} is not a subclass of {other.resource_types}")

        self._next.append(other)
        other._prev = self

        # Nested import to prevent cyclic dependency
        from ..io.connector import Connector
        return Connector(out_port=self, in_port=other)

    def __or__(self, other: 'InPort'):
        """
        Connection operator.

        Alias of :meth:`pipe`
        """

        return self.pipe(other)

    @property
    def name(self) -> str:
        """
        Returns the name of the port.

        :return: The name
        :rtype: str
        """

        proc = self.parent.parent
        input = proc.output
        for name in input._ports:
            if input._ports[name] is self:
                return name
        return None
