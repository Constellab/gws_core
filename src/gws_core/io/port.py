
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Type, final

from ..core.exception.exceptions import BadRequestException
from ..core.model.base import Base
from ..resource.resource import Resource

if TYPE_CHECKING:
    from ..process.processable_model import ProcessableModel
    from .io import IO


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    _resource: Resource = None
    _resource_types: Tuple[Type[Resource]] = ()
    _prev: 'Port' = None
    _next: List['Port'] = []
    _parent: IO

    def __init__(self, parent: IO):
        self._resource = None
        self._prev = None
        self._next = []
        self._parent = parent

        self._resource_types = Resource

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
        return self._resource_types[0]

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
        return isinstance(self._resource, self._resource_types)

    @property
    def is_optional(self) -> bool:
        """
        Returns True if the resource in this port is optional, False otherwise

        :return: True if the resource is optional, False otherwise.
        :rtype: bool
        """

        return (None in self._resource_types)

    @property
    def is_empty(self) -> bool:
        return self._resource is None

    # -- G --

    def get_next_procs(self):
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
    def next(self) -> 'Port':
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
            port._resource = self._resource

    def __or__(self, other: 'Port'):
        raise BadRequestException(
            "Port cannot be . Use InPort or OutPort class")

    # -- R --

    def _reset(self):
        self._resource = None
        # for port in self._next:
        #    port._resource = None

    @property
    def resource(self) -> Resource:
        """
        Returns the resoruce of the port.

        :return: The resource
        :rtype: Resource
        """

        return self._resource

    # -- S --
    @resource.setter
    def resource(self, resource: Resource):
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: Resource
        """

        if self.is_optional and resource is None:
            return

        if not isinstance(resource, self._resource_types):
            raise BadRequestException(
                f"The resource must be an instance of Resource. A {self._resource_types} is given.")

        self._resource = resource


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
        input = proc.input
        for name in input._ports:
            if input._ports[name] is self:
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

    def _are_compatible_types(self, left_types, right_types):
        OK = False
        for t in left_types:
            if issubclass(t, right_types):
                OK = True
                break

        return OK

    def pipe(self, other: 'InPort', lazy: bool = False):
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
            if not self._are_compatible_types(self._resource_types, other._resource_types):
                raise BadRequestException(
                    f"Invalid connection. {self._resource_types} is not a subclass of {other._resource_types}")

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
