# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws.base import Base
from gws.logger import Error

class Port(Base):
    """
    Port class. 
    
    A port contains a resource and allows connecting processes.
    Example: [Left Process]-<output port> ---> <input port>-[Right Process]. 
    """

    _resource_type: 'Resource'
    _resource: 'Resource'
    _prev: 'Port' = None
    _next: list = []
    _parent: 'IO'

    def __init__(self, parent: 'IO'):
        self._resource = None
        self._next = []
        self._parent = parent

        from gws.model import Resource
        self._resource_type = Resource

    
    # -- I -- 

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
    def is_ready(self)->bool:
        """
        Returns True if the port is ready (i.e. contains a resource), False otherwise.

        :return: True if the port is ready, False otherwise.
        :rtype: bool
        """
        return isinstance(self._resource, self._resource_type) and self._resource.is_saved()

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
        raise Error(self.classname(), "|", f"Port cannot be . Use InPort or OutPort class")
    
    # -- R -- 

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

        from gws.model import Resource
        if not isinstance(resource, Resource):
            raise Error(self.classname(), "resource", "The resource must be an instance of Resource")

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
        raise Error(self.classname(), "|", f"The input port cannot be connected on the right")


# ####################################################################
#
# OutPort class
#
# ####################################################################

class OutPort(Port):
    """ 
    OutPort class representing output port
    """

    def pipe(self, other: 'InPort'):
        """ 
        Connection operator.

        Connect the output port to another (right-hand side) input port.
        :return: The right-hand sode port
        :rtype: Port
        """
        if not isinstance(other, InPort):
            raise Error(self.classname(), "|", "The output port can only be connected to an input port")

        if other.is_left_connected:
            raise Error(self.classname(), "|", f"The right-hand side port is already connected")

        if self == other:
            raise Error(self.classname(), "|", "Self connection not allowed")
        
        if not issubclass(self._resource_type, other._resource_type):
            raise Error(self.classname(), "|", f"Invalid connection. {self._resource_type} is not a subclass of {other._resource_type}")

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
    name:str = None
    source_port:Port = None
    target_port:Port = None
    
    def __init__(self, name: str, source_port : Port, target_port: Port):
        if not isinstance(source_port, Port):
            raise Error("Interface", "__init__", "The source port must be a port")
            
        if not isinstance(target_port, Port):
            raise Error("Interface", "__init__", "The target port must be a port")
            
        self.name = name 
        self.source_port = source_port
        self.target_port = target_port
        
    def as_json(self):
        return {
            "name": self.name,
            "from": {
                "node": self.source_port.process.active_name,
                "port": self.source_port.name,
            },
            
            "to": {
                "node": self.target_port.process.active_name,
                "port": self.target_port.name,
            }
        }
    
class Interface(IOface):
    source_port:InPort = None
    target_port:InPort = None
        
    def __init__(self, name: str, source_port : InPort, target_port: InPort):
        
        if not isinstance(source_port, InPort):
            raise Error("Interface", "__init__", "The source port must be an input port")
            
        if not isinstance(target_port, InPort):
            raise Error("Interface", "__init__", "The target port must be an input port")
            
        super().__init__(name, source_port, target_port)
    
        
class Outerface(IOface):
    source_port:OutPort = None
    target_port:OutPort = None
        
    def __init__(self, name: str, source_port : OutPort, target_port : OutPort):
        
        if not isinstance(source_port, OutPort):
            raise Error("Outerface", "__init__", "The source port must be an output port")
        
        if not isinstance(target_port, OutPort):
            raise Error("Outerface", "__init__", "The target port must be an output port")
            
        super().__init__(name, source_port, target_port)

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

    def __init__(self, out_port: OutPort = None, in_port : InPort = None):
        if not isinstance(in_port, InPort):
            raise Error("Connector", "__init__", "The input port must be an instance of InPort")
        
        if not isinstance(out_port, OutPort):
            raise Error("Connector", "__init__", "The output port must be an instance of OutPort")
        
        source_process = out_port.parent.parent
        target_process = in_port.parent.parent
        
        if in_port.parent is None or target_process is None:
            raise Error("Connector", "__init__", "The input port is not associated with a process")
        
        if out_port.parent is None or source_process is None:
            raise Error("Connector", "__init__", "The output port is not associated with a process")
        
        #if not target_process.active_name:
        #    raise Error("Connector", "__init__", "The target process has no active name")
        #    
        #if not source_process.active_name:
        #    raise Error("Connector", "__init__", "The soruce process has no active name")
        
        self.in_port = in_port
        self.out_port = out_port
    
    # -- A --
    
    def as_json(self) -> dict:
        """
        Returns a dictionnary describing the Connector.

        :return: A dictionnary describing the Connector
        :rtype: dict
        """

        link = {
            "from": {
                "node": self.left_process.active_name,
                "port": self.out_port.name, 
            },
            "to": {
                "node": self.right_process.active_name,  
                "port": self.in_port.name, 
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

    def __init__(self, parent: 'Process'):
        self._parent = parent
        self._ports = dict()
    
    # -- A --
    
    def as_json(self, bare=False):
        _json = {}
        for k in self._ports:
            port = self._ports[k]
            _json[k] = port._resource_type.full_classname()
            #_json[k] = {
            #    "uri": ("" if (bare or not port._resource) else port._resource.uri),
            #    "type": port._resource_type.full_classname()
            #}
            
        return _json
    
    # -- C --

    def create_port(self, name: str, resource_type: type):
        """ 
        Creates a port.

        :param name: Name of the port
        :type name: str
        :param resource_type: The expected type of the resoruce of the port
        :type resource_type: type
        """
        from gws.model import Resource
        if not isinstance(name, str):
            raise Error(self.classname(), "create_port", "Invalid port specs. The port name must be a string")

        if not isinstance(resource_type, type):
            raise Error(self.classname(), "create_port", "Invalid port specs. The resource_type must be type. Maybe you provided an object instead of object type.")
        
        if not issubclass(resource_type, Resource):
            raise Error(self.classname(), "create_port", "Invalid port specs. The resource_type must refer to subclass of Resource")
        
        if self._parent.is_running or self._parent.is_finished:
            raise Error(self.classname(), "__setitem__", "Cannot alter inputs/outputs of processes during or after running")
        
        if type(self) == Output:
            port = OutPort(self)
        else:
            port = InPort(self)

        port._resource_type = resource_type
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
            raise Error(self.classname(), "__getitem__", "The port name must be a string")

        if self._ports.get(name, None) is None:
            raise Error(self.classname(), "__getitem__", self.classname() +" port '"+name+"' not found")

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

    # -- I --

    @property
    def is_ready(self)->bool:
        """
        Returns True if the IO is ready (i.e. all its ports are ready), False otherwise.

        :return: True if the IO is ready, False otherwise.
        :rtype: bool
        """
        for k in self._ports:
            if not self._ports[k].is_ready:
                return False
        return True

    # -- N --

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

    # -- S --

    def __setitem__(self, name: str, resource: 'Resource'):
        """ 
        Bracket (setter) operator. Sets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        """
        if not isinstance(name, str):
            raise Error(self.classname(), "__setitem__", "The port name must be a string")

        if self._ports.get(name, None) is None:
            raise Error(self.classname(), "__setitem__", self.classname() +" port '"+name+"' not found")
        
        self._ports[name].resource = resource
    

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

    def __setitem__(self, name: str, resource: 'Resource'):
        """ 
        Bracket (setter) operator. Sets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        """
        if self._parent.is_running:
            raise Error(self.classname(), "__setitem__", "Cannot alter the input of process while running")

        super().__setitem__(name,resource)

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

    def __setitem__(self, name: str, resource: 'Resource'):
        """ 
        Bracket (setter) operator. Sets the content of a port by its name.

        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        """
        if self._parent.is_finished:
            raise Error(self.classname(), "__setitem__", "Cannot alter the output of a process after running")

        super().__setitem__(name,resource)
        