

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Dict, Generic, List, Type, TypeVar, final

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..model.typing_manager import TypingManager
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel
from ..task.task_io import TaskInputs
from .io_exception import (MissingInputResourcesException,
                           ResourceNotCompatibleException)
from .io_spec import IOSpec
from .port import InPort, OutPort, Port, PortDict

if TYPE_CHECKING:
    from ..process.process_model import ProcessModel

IODict = Dict[str, PortDict]

# For generic Port type
PortType = TypeVar('PortType', bound=Port)


####################################################################
#
# IO class
#
# ####################################################################
class IO(Base, Generic[PortType]):
    """
    Base IO class. The IO class defines base functionalitie for the
    Input and Output classes. A IO is a set of ports.
    """

    _ports: Dict[str, PortType] = {}
    _parent: ProcessModel
    _counter = 0

    def __init__(self, parent: ProcessModel):
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

    def create_port(self, name: str, resource_spec: IOSpec):
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

        port: PortType = self._create_port(resource_spec)
        self._ports[name] = port

    @abstractmethod
    def _create_port(self, resource_spec: IOSpec):
        pass

    # -- G --

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

    def get_port(self, port_name: str) -> PortType:
        """
        Returns the resources of all the ports.

        :return: List of resources
        :rtype: list
        """
        self._check_port_name(port_name)
        return self._ports[port_name]

    # -- I --

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

    def get_next_procs(self) -> List[ProcessModel]:
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
    def ports(self) -> Dict[str, PortType]:
        """
        Returns the list of ports.

        :return: List of port
        :rtype: list
        """

        return self._ports

    @property
    def parent(self) -> ProcessModel:
        """
        Returns the parent of the IO, i.e. the task that holds this IO.

        :return: The parent task
        :rtype: Task
        """

        return self._parent

    def port_exists(self, name: str) -> bool:
        return name in self._ports

    # -- R --

    def reset(self) -> None:
        for port in self._ports.values():
            port.reset()

    # -- S --

    def set_resource_model(self, port_name: str, resource_model: ResourceModel) -> None:
        """Set the resource_model of a port
        """
        port: PortType = self.get_port(port_name)

        resource_type: Type[Resource] = type(resource_model.get_resource())
        if not port.resource_type_is_compatible(resource_type):
            raise ResourceNotCompatibleException(port_name=port_name, resource_type=resource_type,
                                                 spec=port.resource_spec)

        port.resource_model = resource_model

    def get_resource_model(self, port_name: str) -> ResourceModel:
        """Get the resource_model of a port
        """
        port: PortType = self.get_port(port_name)
        return port.resource_model

    def _set_resource_model_without_check(self, port_name: str, resource_model: ResourceModel) -> None:
        """Set the resource in the port without checking the port type
        """
        port: PortType = self.get_port(port_name)
        port.resource_model = resource_model

    def _check_port_name(self, name) -> None:

        error: str = None
        if not isinstance(name, str):
            error = f"The port name must be a string. Actual value: '{name}'"

        if not self.port_exists(name):
            error = f"{self.classname()} port '{name}' not found"

        if error:
            if self.parent:
                error += f" | Task : {self.parent.get_info()}"
            raise BadRequestException(error)

    # -- V --

    def load_from_json(self, io_json: IODict) -> None:
        if input is None:
            return

        for key, port_dict in io_json.items():
            # If the port does not exist, create it
            if not self.port_exists(key):
                resource_types: List[Type[Resource]] = []
                for resource_typing_name in port_dict["specs"]:
                    resource_types.append(TypingManager.get_type_from_name(resource_typing_name))

                self.create_port(key, resource_types)

            # Add resource if provided
            if port_dict["resource"]["typing_name"] and port_dict["resource"]["uri"]:
                resource: ResourceModel = TypingManager.get_object_with_typing_name_and_uri(
                    port_dict["resource"]["typing_name"], port_dict["resource"]["uri"])
                self._set_resource_model_without_check(key, resource)

    def to_json(self) -> IODict:
        _json = {}

        for key, port in self._ports.items():
            _json[key] = port.to_json()
        return _json

# ####################################################################
#
# Input class
#
# ####################################################################


@final
class Inputs(IO[InPort]):
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

    def _create_port(self, resource_spec: IOSpec) -> InPort:
        return InPort(self, resource_spec)

    def all_connected_port_values_provided(self) -> bool:
        """Return true if all the ports that are connected, received a resource
        """
        for port in self.ports.values():
            if port.is_left_connected and not port.resource_provided:
                return False

        return True

    def get_and_check_task_inputs(self) -> TaskInputs:
        """Get the task inputs and check all the mandatory inputs are provided

        :return: [description]
        :rtype: ProcessIO
        """
        missing_resource: List[str] = []
        task_io: TaskInputs = TaskInputs()
        for key, port in self.ports.items():

            if port.is_empty:
                # If the port is empty and not optional, add an error
                if not port.is_optional:
                    missing_resource.append(key)
                continue
            # get the port resource and force a new instance to prevent modifing the same
            # resource on new task
            task_io[key] = port.get_resource(new_instance=True)

        if len(missing_resource) > 0:
            raise MissingInputResourcesException(port_names=missing_resource)

        return task_io

# ####################################################################
#
# Output class
#
# ####################################################################


@final
class Outputs(IO[OutPort]):
    """
    Output class
    """

    def _create_port(self, resource_spec: IOSpec) -> OutPort:
        return OutPort(self, resource_spec)

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
