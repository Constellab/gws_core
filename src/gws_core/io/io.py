

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple, final

from gws_core.process.process_io import ProcessIO

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..resource.resource_model import ResourceModel
from .io_types import IOSpec
from .port import InPort, OutPort, Port

if TYPE_CHECKING:
    from ..process.processable_model import ProcessableModel


####################################################################
#
# IO class
#
# ####################################################################
class IO(Base):
    """
    Base IO class. The IO class defines base functionalitie for the
    Input and Output classes. A IO is a set of ports.
    """

    _ports: Dict[str, Port] = {}
    _parent: ProcessableModel
    _counter = 0

    def __init__(self, parent: ProcessableModel):
        self._parent = parent
        self._ports = dict()

    # -- D --

    def disconnect(self):
        """
        Disconnect the IO
        """

        for port in self._ports.values():
            port.disconnect()

    # -- C --

    def create_port(self, name: str, resource_types: IOSpec):
        """
        Creates a port.

        :param name: Name of the port
        :type name: str
        :param resource_types: The expected type of the resource of the port
        :type resource_types: type
        """

        if not isinstance(name, str):
            raise BadRequestException(
                "Invalid port specs. The port name must be a string")

        if self._parent.is_instance_running or self._parent.is_instance_finished:
            raise BadRequestException(
                "Cannot alter inputs/outputs of processes during or after running")

        port: Port
        if isinstance(self, Output):
            port = OutPort(self, resource_types)
        else:
            port = InPort(self, resource_types)

        self._ports[name] = port

    # -- G --

    def __getitem__(self, name: str) -> ResourceModel:
        """
        Bracket (getter) operator. Gets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :return: The resource of the port
        :rtype: ResourceModel
        """

        if not isinstance(name, str):
            raise BadRequestException("The port name must be a string")

        if self._ports.get(name, None) is None:
            raise BadRequestException(
                self.classname() + " port '" + name + "' not found")

        return self._ports[name].resource_model

    def get_port_names(self) -> List[str]:
        """
        Returns the names of all the ports.

        :return: List of names
        :rtype: list
        """

        return list(self._ports.keys())

    def get_resources(self) -> Dict[str, ResourceModel]:
        """
        Returns the resources of all the ports.

        :return: List of resources
        :rtype: list
        """

        resource_models: Dict[str, ResourceModel] = {}
        for key, port in self._ports.items():
            resource_models[key] = port.resource_model
        return resource_models

    def get_port(self, port_name: str) -> Port:
        """
        Returns the resources of all the ports.

        :return: List of resources
        :rtype: list
        """

        return self._ports[port_name]

    def get_specs(self) -> Dict[str, Tuple[str]]:
        specs: Dict[str, Tuple[str]] = {}

        for key, port in self._ports.items():
            specs[key] = ()

            for resource_type in port.resource_types:
                if resource_type is None:
                    specs[key] += (None,)
                else:
                    classname = resource_type._typing_name
                    specs[key] += (classname,)

        return specs

    # -- I --

    # Creates iterator object
    # Called when iteration is initialized
    def __iter__(self):
        return self._ports.__iter__()

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the IO is ready (i.e. all its ports are ready), False otherwise.

        :return: True if the IO is ready, False otherwise.
        :rtype: bool
        """

        for port in self._ports.values():
            if not port.is_ready:
                return False

        return True

    @property
    def is_empty(self) -> bool:
        for port in self._ports.values():
            if not port.is_empty:
                return False
        return True

    # -- N --

    def __next__(self):
        return self._ports.__next__()

    def get_next_procs(self) -> List[ProcessableModel]:
        """
        Returns the list of (right-hand side) processes connected to the IO ports.

        :return: List of processes
        :rtype: list
        """

        next_proc = []
        for port in self._ports.values():
            for proc in port.get_next_procs():
                next_proc.append(proc)
        return next_proc

    # -- P --

    @property
    def ports(self) -> Dict[str, Port]:
        """
        Returns the list of ports.

        :return: List of port
        :rtype: list
        """

        return self._ports

    @property
    def parent(self) -> ProcessableModel:
        """
        Returns the parent of the IO, i.e. the process that holds this IO.

        :return: The parent process
        :rtype: Process
        """

        return self._parent

    # -- R --

    def reset(self) -> None:
        for port in self._ports.values():
            port.reset()

    # -- S --

    def __setitem_without_check__(self, name: str, resource: ResourceModel):
        if not isinstance(name, str):
            raise BadRequestException("The port name must be a string")

        if self._ports.get(name, None) is None:
            raise BadRequestException(
                self.classname() + " port '" + name + "' not found")

        self._ports[name].resource_model = resource

    def __setitem__(self, name: str, resource: ResourceModel):
        """
        Bracket (setter) operator. Sets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: ResourceModel
        """

        # if self._parent.is_running:
        #    raise BadRequestException("Cannot alter the input of process while it is running")

        self.__setitem_without_check__(name, resource)

    def get_process_io(self) -> ProcessIO:
        process_io: ProcessIO = {}
        for key, port in self.ports.items():
            process_io[key] = port.get_resource()
        return process_io

    # -- V --

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = {}

        for k in self._ports:
            port = self._ports[k]
            _json[k] = {}

            if port.resource_model:
                _json[k]["resource"] = {
                    "uri": port.resource_model.uri,
                    "typing_name": port.resource_model.resource_typing_name
                }
            else:
                _json[k]["resource"] = {
                    "uri": "",
                    "typing_name": ""
                }

            specs: List[str] = []
            for resource_type in port.resource_types:
                if resource_type is None:
                    specs.append(None)
                else:
                    specs.append(resource_type._typing_name)
            _json[k]["specs"] = specs

        return _json

# ####################################################################
#
# Input class
#
# ####################################################################


@final
class Input(IO):
    """
    Input class
    """

    @property
    def is_connected(self) -> bool:
        """
        Returns True if a port of the Input is left-connected.

        :return: True if a port of the Input is left-connected.
        :rtype: bool
        """

        for port in self._ports.values():
            if not port.is_left_connected:
                return False

        return True

# ####################################################################
#
# Output class
#
# ####################################################################


@final
class Output(IO):
    """
    Output class
    """

    @property
    def is_connected(self) -> bool:
        """
        Returns True if a port of the Output is right-connected.

        :return: True if a port of the Output is right-connected.
        :rtype: bool
        """
        for port in self._ports.values():
            if not port.is_right_connected:
                return False

        return True

    def propagate(self):
        """
        Propagates the resources of the child port to the connected (right-hande side) ports
        """

        for port in self._ports.values():
            port.propagate()
