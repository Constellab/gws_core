# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..core.exception.exceptions import BadRequestException
from ..core.model.base import Base
from .resource import Resource


class Port(Base):
    """
    Port class

    A port contains a resource and allows connecting processes.
    Example: [Left Process](output port) => (input port)[Right Process].
    """

    _resource: 'Resource' = None
    _resource_types: tuple = ()
    _prev: 'Port' = None
    _next: list = []
    _parent: 'IO'

    def __init__(self, parent: 'IO'):
        self._resource = None
        self._prev = None
        self._next = []
        self._parent = parent

        self._resource_types = (Resource, )

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
    def parent(self) -> 'IO':
        """
        Returns the parent IO of the Port, i.e. the IO (Input or Output) that holds this Port.

        :return: The parent IO
        :rtype: IO
        """
        return self._parent

    @property
    def process(self) -> 'Process':
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
    def resource(self) -> 'Resource':
        """
        Returns the resoruce of the port.

        :return: The resource
        :rtype: Resource
        """

        return self._resource

    # -- S --
    @resource.setter
    def resource(self, resource: 'Resource'):
        """
        Sets the resource of the port.

        :param resource: The input resource
        :type resource: Resource
        """

        if self.is_optional and resource is None:
            return

        from .resource import Resource
        if not isinstance(resource, self._resource_types):
            raise BadRequestException(
                f"The resource must be an instance of Resource. A {self._resource_types} is given.")

        self._resource = resource


# ####################################################################
#
# InPort class
#
# ####################################################################

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

    def __or__(self, other: 'Port'):
        raise BadRequestException(
            f"The input port cannot be connected on the right")


# ####################################################################
#
# OutPort class
#
# ####################################################################

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


class IOface:
    name: str = None
    source_port: Port = None
    target_port: Port = None

    def __init__(self, name: str, source_port: Port, target_port: Port):
        if not isinstance(source_port, Port):
            raise BadRequestException("The source port must be a port")

        if not isinstance(target_port, Port):
            raise BadRequestException("The target port must be a port")

        self.name = name
        self.source_port = source_port
        self.target_port = target_port

    # -- D --

    def disconnect(self):
        """
        Disconnect the IOFace
        """

        if self.source_port:
            self.source_port.disconnect()

        if self.target_port:
            self.target_port.disconnect()

    # -- R --

    def _reset(self):
        if self.source_port:
            self.source_port._reset()

        if self.target_port:
            self.target_port._reset()

    # -- T --

    def to_json(self, **kwargs):
        bare = kwargs.get("bare", False)
        r_uri = ""
        r_type = ""
        if self.source_port.resource and not bare:
            r_uri = self.source_port.resource.uri
            r_type = self.source_port.resource.type

        return {
            "name": self.name,
            "from": {
                "node": self.source_port.process.instance_name,
                "port": self.source_port.name,
            },
            "to": {
                "node": self.target_port.process.instance_name,
                "port": self.target_port.name,
            },
            "resource": {
                "uri": r_uri,
                "type": r_type
            }
        }


class Interface(IOface):
    source_port: InPort = None
    target_port: InPort = None

    def __init__(self, name: str, source_port: InPort, target_port: InPort):

        if not isinstance(source_port, InPort):
            raise BadRequestException("The source port must be an input port")

        if not isinstance(target_port, InPort):
            raise BadRequestException("The target port must be an input port")

        super().__init__(name, source_port, target_port)

    # -- S --

    def set_resource(self, resource: 'Resource'):
        self.source_port.resource = resource
        self.target_port.resource = resource

    # -- V -

    def to_json(self, **kwargs):
        _json = super().to_json(**kwargs)
        _json["from"]["node"] = ":parent:"
        return _json


class Outerface(IOface):
    source_port: OutPort = None
    target_port: OutPort = None

    def __init__(self, name: str, source_port: OutPort, target_port: OutPort):

        if not isinstance(source_port, OutPort):
            raise BadRequestException("The source port must be an output port")

        if not isinstance(target_port, OutPort):
            raise BadRequestException("The target port must be an output port")

        super().__init__(name, source_port, target_port)

    # -- G --

    def get_resource(self) -> 'Resource':
        return self.source_port.resource

    # -- V --

    def to_json(self, **kwargs):
        _json = super().to_json(**kwargs)
        _json["to"]["node"] = ":parent:"
        return _json

# ####################################################################
#
# Connector class
#
# ####################################################################


class Connector:
    """
    Connector class representing the connection of two Ports.

    :param in_port: Left-hand side in_port
    :type in_port: InPort
    :param out_port: Right-hand side out_port
    :type out_port: OutPort
    """

    in_port = None
    out_port = None

    def __init__(self, out_port: OutPort = None, in_port: InPort = None):
        if not isinstance(in_port, InPort):
            raise BadRequestException(
                "The input port must be an instance of InPort")

        if not isinstance(out_port, OutPort):
            raise BadRequestException(
                "The output port must be an instance of OutPort")

        source_process = out_port.parent.parent
        target_process = in_port.parent.parent

        if in_port.parent is None or target_process is None:
            raise BadRequestException(
                "The input port is not associated with a process")

        if out_port.parent is None or source_process is None:
            raise BadRequestException(
                "The output port is not associated with a process")

        # if not target_process.instance_name:
        #    raise BadRequestException("The target process has no active name")
        #
        # if not source_process.instance_name:
        #    raise BadRequestException("The soruce process has no active name")

        self.in_port = in_port
        self.out_port = out_port

    # -- V --

    def to_json(self, **kwargs) -> dict:
        """
        Returns a dictionnary describing the Connector.

        :return: A dictionnary describing the Connector
        :rtype: dict
        """

        bare = kwargs.get("bare", False)

        r_uri = ""
        r_type = ""

        if self.out_port.resource and not bare:
            r_uri = self.out_port.resource.uri
            r_type = self.out_port.resource.type

        link = {
            "from": {
                "node": self.left_process.instance_name,
                "port": self.out_port.name,
            },
            "to": {
                "node": self.right_process.instance_name,
                "port": self.in_port.name,
            },
            "resource": {
                "uri": r_uri,
                "type": r_type
            }
        }

        return link

    # -- L --

    @property
    def left_process(self) -> 'Process':
        """
        Returns the left-hand side process

        :return: The left-hand side process
        :rtype: Process
        """
        return self.out_port.parent.parent

    # -- L --

    # -- O --

    @property
    def right_process(self) -> 'Process':
        """
        Returns the right-hand side process

        :return: The right-hand side process
        :rtype: Process
        """
        return self.in_port.parent.parent

# ####################################################################
#
# IO class
#
# ####################################################################


class IO(Base):
    """
    Base IO class. The IO class defines base functionalitie for the
    Input and Output classes. A IO is a set of ports.
    """

    _ports: dict = {}
    _parent: 'Process'
    _counter = 0

    def __init__(self, parent: 'Process'):
        self._parent = parent
        self._ports = dict()

    # -- D --

    def disconnect(self):
        """
        Disconnect the IO
        """

        for k in self._ports:
            self._ports[k].disconnect()

    # -- C --

    def create_port(self, name: str, resource_types: type):
        """
        Creates a port.

        :param name: Name of the port
        :type name: str
        :param resource_types: The expected type of the resource of the port
        :type resource_types: type
        """

        from .resource import Resource
        if not isinstance(name, str):
            raise BadRequestException(
                "Invalid port specs. The port name must be a string")

        if isinstance(resource_types, tuple):
            for res_t in resource_types:
                if (not res_t is None) and not issubclass(res_t, Resource):
                    raise BadRequestException(
                        "Invalid port specs. The resource_types must refer to a subclass of Resource")
        else:
            if not issubclass(resource_types, Resource):
                raise BadRequestException(
                    "Invalid port specs. The resource_types must refer to a subclass of Resource")

            resource_types = (resource_types, )

        if self._parent.is_instance_running or self._parent.is_instance_finished:
            raise BadRequestException(
                "Cannot alter inputs/outputs of processes during or after running")

        if type(self) == Output:
            port = OutPort(self)
        else:
            port = InPort(self)

        port._resource_types = resource_types
        self._ports[name] = port

    # -- G --

    def __getitem__(self, name: str) -> 'Resource':
        """
        Bracket (getter) operator. Gets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :return: The resource of the port
        :rtype: Resource
        """

        if not isinstance(name, str):
            raise BadRequestException("The port name must be a string")

        if self._ports.get(name, None) is None:
            raise BadRequestException(
                self.classname() + " port '"+name+"' not found")

        return self._ports[name].resource

    def get_port_names(self) -> list:
        """
        Returns the names of all the ports.

        :return: List of names
        :rtype: list
        """

        return list(self._ports.keys)

    def get_resources(self) -> dict:
        """
        Returns the resources of all the ports.

        :return: List of resources
        :rtype: list
        """

        resources = {}
        for k in self._ports:
            resources[k] = self._ports[k].resource
        return resources

    def get_specs(self):
        specs = {}

        for k in self._ports:
            port = self._ports[k]
            specs[k] = ()

            for t in port._resource_types:
                if t is None:
                    specs[k] += (None, )
                else:
                    classname = t.full_classname()
                    specs[k] += (classname, )

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

        for k in self._ports:
            if not self._ports[k].is_ready:
                return False

        return True

    @property
    def is_empty(self) -> bool:
        for k in self._ports:
            if not self._ports[k].is_empty:
                return False

    # -- N --

    def __next__(self):
        return self._ports.__next__()

    def get_next_procs(self) -> list:
        """
        Returns the list of (right-hand side) processes connected to the IO ports.

        :return: List of processes
        :rtype: list
        """

        next_proc = []
        for k in self._ports:
            for proc in self._ports[k].get_next_procs():
                next_proc.append(proc)
        return next_proc

    # -- P --

    @property
    def ports(self) -> dict:
        """
        Returns the list of ports.

        :return: List of port
        :rtype: list
        """

        return self._ports

    @property
    def parent(self) -> 'Process':
        """
        Returns the parent of the IO, i.e. the process that holds this IO.

        :return: The parent process
        :rtype: Process
        """

        return self._parent

    # -- R --

    def _reset(self):
        for k in self._ports:
            self._ports[k]._reset()

    # -- S --

    def __setitem_without_check__(self, name: str, resource: 'Resource'):
        if not isinstance(name, str):
            raise BadRequestException("The port name must be a string")

        if self._ports.get(name, None) is None:
            raise BadRequestException(
                self.classname() + " port '"+name+"' not found")

        self._ports[name].resource = resource

    def __setitem__(self, name: str, resource: 'Resource'):
        """
        Bracket (setter) operator. Sets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        """

        # if self._parent.is_running:
        #    raise BadRequestException("Cannot alter the input of process while it is running")

        self.__setitem_without_check__(name, resource)

    # -- V --

    def to_json(self, **kwargs):
        _json = {}
        bare = kwargs.get("bare")

        for k in self._ports:
            port = self._ports[k]
            _json[k] = {}

            if port.resource and not bare:
                _json[k]["resource"] = {
                    "uri": port.resource.uri,
                    "type": port.resource.type
                }
            else:
                _json[k]["resource"] = {
                    "uri": "",
                    "type": ""
                }

            _json[k]["specs"] = ()
            for t in port._resource_types:
                if t is None:
                    _json[k]["specs"] += (None, )
                else:
                    classname = t.full_classname()
                    _json[k]["specs"] += (classname, )

        return _json

# ####################################################################
#
# Input class
#
# ####################################################################


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

        for k in self._ports:
            if not self._ports[k].is_left_connected:
                return False

        return True

# ####################################################################
#
# Output class
#
# ####################################################################


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
        for k in self._ports:
            if not self._ports[k].is_right_connected:
                return False

        return True

    def propagate(self):
        """
        Propagates the resources of the child port sto the connected (right-hande side) ports
        """

        for k in self._ports:
            self._ports[k].propagate()