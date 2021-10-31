# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING, List, Type, TypedDict, final

from ..core.model.base import Base
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from .io_spec import IOSpec, IOSpecClass, IOSpecsHelper

if TYPE_CHECKING:
    from ..process.process_model import ProcessModel
    from .io import IO


class PortResourceDict(TypedDict):
    uri: str
    typing_name: str


class PortDict(TypedDict):
    resource: PortResourceDict
    specs: List[str]  # list of supported resource typing names


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    _resource_model: ResourceModel = None
    _resource_spec: IOSpecClass = None
    _prev: 'Port' = None
    _next: List['Port'] = []
    _parent: IO

    # Switch to true when the set_resource_model is set (even if it is set with a None value)
    _resource_provided: bool = False

    def __init__(self, parent: IO, _resource_spec: IOSpec):
        self._resource_model = None
        self._prev = None
        self._next = []
        self._parent = parent

        self.set_resource_spec(_resource_spec)

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

        # If the type is skippable, the port is always ready
        if self.is_skippable_in:
            return True

        if self.is_optional:
            # If the port is connected but the set_resource was not called,
            # the port is not ready
            if self.is_left_connected and not self._resource_provided:
                return False
            else:
                return True

        return self._resource_provided

    @property
    def is_optional(self) -> bool:
        """
        Returns True if the resource in this port is optional (optional or skippable), False otherwise

        :return: True if the resource is optional, False otherwise.
        :rtype: bool
        """

        return self.resource_spec.is_optional()

    @property
    def is_empty(self) -> bool:
        return self._resource_model is None

    @property
    def is_unmodified_out(self) -> bool:
        """return true if the port type is ConstantOut

        :return: [description]
        :rtype: bool
        """
        return self.resource_spec.is_unmodified_out()

    @property
    def is_skippable_in(self) -> bool:
        """return true if the port type is SKippableIn

        :return: [description]
        :rtype: bool
        """
        return self.resource_spec.is_skippable_in()

    @property
    def resource_provided(self) -> bool:
        """
        Returns True if the resource of the port was provided
        """

        return self._resource_provided

    # -- G --

    def get_next_procs(self) -> List[ProcessModel]:
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

    def add_next(self, port: 'Port') -> None:
        self._next.append(port)

    def set_previous(self, port: 'Port') -> None:
        self._prev = port

    @property
    def parent(self) -> IO:
        """
        Returns the parent IO of the Port, i.e. the IO (Input or Output) that holds this Port.

        :return: The parent IO
        :rtype: IO
        """
        return self._parent

    @property
    def process(self) -> ProcessModel:
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

    # -- R --

    def reset(self):
        self._resource_model = None
        self._resource_provided = False

    @property
    def resource_spec(self) -> IOSpecClass:
        """
        Returns the resource types of the port.

        :return: The resource
        :rtype: ResourceModel
        """

        return self._resource_spec

    # -- S --

    def set_resource_spec(self, resource_spec: IOSpec):
        """
        Sets the resource_types of the port.

        :param resource: The input resource
        :type resource: Resource
        """

        self._resource_spec = IOSpecClass(spec=resource_spec)

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
    def resource_model(self, resource_model: ResourceModel) -> None:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """
        # mark the resource as provided
        self._resource_provided = True
        self._resource_model = resource_model

    # -- S --
    def resource_type_is_compatible(self, resource_type: Type[Resource]) -> bool:
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: ResourceModel
        """

        if self.is_optional and resource_type is None:
            return True

        return IOSpecsHelper.spec_is_compatible(resource_type, self._resource_spec.resource_spec)

    def get_resource(self, new_instance: bool = False) -> Resource:
        return self.resource_model.get_resource(new_instance=new_instance)

    @property
    def name(self) -> str:
        """overiden by the children

        """
        pass

    def to_json(self) -> PortDict:
        _json: PortDict = {"resource": None, "specs": None}

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

        _json["specs"] = self.resource_spec.to_json()
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
        proc_inputs = proc.inputs
        for name in proc_inputs._ports:
            if proc_inputs._ports[name] is self:
                return name
        return None


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

    @property
    def name(self) -> str:
        """
        Returns the name of the port.

        :return: The name
        :rtype: str
        """

        proc = self.parent.parent
        proc_outputs = proc.outputs
        for name in proc_outputs._ports:
            if proc_outputs._ports[name] is self:
                return name
        return None
