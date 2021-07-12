# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import zlib
from datetime import datetime

from peewee import BooleanField

from .user import User
from .logger import Error
from .process import Process
from .io import Input, Output, InPort, OutPort, Interface, Outerface, Connector

class Protocol(Process):
    """
    Protocol class.

    :property processes: Dictionnary of processes
    :type processes: dict
    :property connectors: List of connectors represinting process connection
    :type connectors: list
    """

    is_template = BooleanField(default=False, index=True)

    _is_singleton = False
    _processes: dict = {}
    _connectors: list = []
    _interfaces: dict = {}
    _outerfaces: dict = {}
    _defaultPosition: list = [0.0, 0.0]

    _table_name = "gws_protocol"

    def __init__(self, *args, processes: dict = {}, \
                 connectors: list = [], interfaces: dict = {}, outerfaces: dict = {}, \
                 user = None, **kwargs):

        super().__init__(*args, user = user, **kwargs)
        self._input = Input(self)
        self._output = Output(self)
        self._processes = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}
        self._defaultPosition = [0.0, 0.0]

        if self.uri and self.data.get("graph"):          #the protocol was saved in the super-class
            self._build_from_dump( self.data["graph"] )
        else:
            self._build(
                processes,
                connectors,
                interfaces,
                outerfaces,
                user
            )

    def _init_io(self):
        pass

    # -- A --

    def add_process(self, name: str, process: Process):
        """
        Adds a process to the protocol.

        :param name: Unique name of the process
        :type name: str
        :param process: The process
        :type process: Process
        """

        if not self.id:
            self.save()

        if self.is_instance_finished or self.is_instance_running:
            raise Error("gws.model.Protocol", "add_process", "The protocol has already been run")

        if not isinstance(process, Process):
            raise Error("gws.model.Protocol", "add_process", f"The process '{name}' must be an instance of Process")

        if process.protocol_id and self.id != process.protocol_id:
            raise Error("gws.model.Protocol", "add_process", f"The process instance '{name}' already belongs to another protocol")

        if name in self._processes:
            raise Error("gws.model.Protocol", "add_process", f"Process name '{name}' already exists")

        if process in self._processes.items():
            raise Error("gws.model.Protocol", "add_process", f"Process '{name}' duplicate")

        process.protocol_id = self.id
        process._protocol = self

        if self.experiment_id:
            process.set_experiment(self.experiment)

        process.instance_name = name
        process.save()

        self._processes[name] = process

    def add_connector(self, connector: Connector):
        """
        Adds a connector to the pfrotocol.

        :param connector: The connector
        :type connector: Connector
        """

        if self.is_instance_finished or self.is_instance_running:
            raise Error("gws.model.Protocol", "add_connector", "The protocol has already been run")

        if not isinstance(connector, Connector):
            raise Error("gws.model.Protocol", "add_connector", "The connector must be an instance of Connector")

        if  not connector.left_process in self._processes.values() or \
            not connector.right_process in self._processes.values():
            raise Error("gws.model.Protocol", "add_connector", "The processes of the connector must belong to the protocol")

        if connector in self._connectors:
            raise Error("gws.model.Protocol", "add_connector", "Duplciated connector")

        self._connectors.append(connector)

    def archive(self, tf:bool, archive_resources=True) -> bool:
        """
        Archive the protocol
        """

        if self.is_archived == tf:
            return True

        with self._db_manager.db.atomic() as transaction:
            for k in self._processes:
                proc = self._processes[k]
                if not proc.archive(tf, archive_resources=archive_resources):
                    transaction.rollback()
                    return False

            status = super().archive(tf)
            if not status:
                transaction.rollback()

            return status

    # -- B --

    def _build(self, processes: dict=None, connectors: list=None, interfaces: dict=None, outerfaces: dict=None, user=None, **kwargs):
        if not isinstance(processes, dict):
            raise Error("gws.model.Protocol", "__init__", "A dictionnary of processes is expected")

        if not isinstance(connectors, list):
            raise Error("gws.model.Protocol", "__init__", "A list of connectors is expected")

        # set process
        for name in processes:
            proc = processes[name]
            if not isinstance(proc, Process):
                raise Error("gws.model.Protocol", "__init__", "The dictionnary of processes must contain instances of Process")

            self.add_process(name, proc)

        # set connectors
        for conn in connectors:
            if not isinstance(conn, Connector):
                raise Error("gws.model.Protocol", "__init__", "The list of connector must contain instances of Connectors")

            self.add_connector(conn)

        if user is None:
            try:
                from .service.user_service import UserService
                user = UserService.get_current_user()
            except:
                raise Error("gws.model.Protocol", "__init__", "A user is required")

        if isinstance(user, User):
            if self.created_by.is_sysuser:
                # The sysuser is used by default to create any Process
                # We therefore replace the syssuser by the currently authenticated user

                if user.is_authenticated:
                    self.create_by = user
                else:
                    raise Error("gws.model.Protocol", "__init__", "The user must be authenticated")
        else:
            raise Error("gws.model.Protocol", "__init__", "The user must be an instance of User")

        # set interfaces
        self.__set_interfaces(interfaces)
        self.__set_outerfaces(outerfaces)
        self.data["graph"] = self.dumps(as_dict=True)
        self.save()   #<- will save the graph

    def _build_from_dump( self, graph: (str, dict), rebuild = False ) -> 'Protocol':
        """
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """

        # Do not build the protocol if it is not draft and is already built
        if self.is_built and not self.is_draft:
            return True

        from .service.model_service import ModelService

        if isinstance(graph, str):
            graph = json.loads(graph)

        if not isinstance(graph,dict):
            return

        if not isinstance(graph.get("nodes"), dict) or not graph["nodes"]:
            return

        if rebuild:
            if self.is_draft:
                deleted_keys = []
                for k in self._processes:
                    proc = self._processes[k]

                    is_removed = False
                    if k in graph["nodes"]:
                        if proc.type != graph["nodes"][k].get("type"):
                            is_removed = True
                    else:
                        is_removed = True

                    if is_removed:
                        proc.delete_instance()
                        deleted_keys.append(k)

                    # disconnect the port to prevent connection errors later
                    proc.disconnect()

                for k in deleted_keys:
                    del self._processes[k]

        # will be rebuilt
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}

        # create nodes
        for k in graph["nodes"]:
            node_json = graph["nodes"][k]
            proc_uri = node_json.get("uri",None)
            proc_type_str = node_json["type"]

            try:
                proc_t = ModelService.get_model_type(proc_type_str)

                if proc_t is None:
                    raise Exception(f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")
                else:
                    if proc_uri:
                        proc = proc_t.get(proc_t.uri == proc_uri)
                    else:
                        if issubclass(proc_t, Protocol):
                            proc = Protocol.from_graph( node_json["data"]["graph"] )
                        else:
                            proc = proc_t()

                    if k in self._processes:
                        self._processes[k].data = proc.data #copy current data
                    else:
                        self.add_process( k, proc )

                # update config if required
                config_json = node_json.get("config")
                if config_json:
                    params = config_json.get("data",{}).get("params",{})
                    if k in self._processes:
                        self._processes[k].config.set_params(params)
                    else:
                        proc.config.set_params(params)

                    proc.config.save()
                    proc.save()


            except Exception as err:
                raise Error("gws.model.Protocol", "_build_from_dump", f"An error occured. Error: {err}")

        # create interfaces and outerfaces
        interfaces = {}
        outerfaces = {}
        for k in graph["interfaces"]:
            _to = graph["interfaces"][k]["to"]  #destination port of the interface
            proc_name = _to["node"]
            port_name = _to["port"]
            proc = self._processes[proc_name]
            port = proc.input.ports[port_name]
            interfaces[k] = port

        for k in graph["outerfaces"]:
            _from = graph["outerfaces"][k]["from"]  #source port of the outerface
            proc_name = _from["node"]
            port_name = _from["port"]
            proc = self._processes[proc_name]
            port = proc.output.ports[port_name]
            outerfaces[k] = port

        self.__set_interfaces(interfaces)
        self.__set_outerfaces(outerfaces)

        # create links
        for link in graph["links"]:
            proc_name = link["from"]["node"]
            lhs_port_name = link["from"]["port"]
            lhs_proc = self._processes[proc_name]

            proc_name = link["to"]["node"]
            rhs_port_name = link["to"]["port"]
            rhs_proc = self._processes[proc_name]

            #connector = (lhs_proc>>lhs_port_name | rhs_proc<<rhs_port_name)
            connector = (lhs_proc>>lhs_port_name).pipe(rhs_proc<<rhs_port_name, lazy=True)
            self.add_connector(connector)

        self.save(update_graph=True)

    # -- C --

    @classmethod
    def create_process_type(cls):
        from .typing import ProtocolType
        exist = ProtocolType.select().where(ProtocolType.model_type == cls.full_classname()).count()
        if not exist:
            pt = ProtocolType(
                model_type = cls.full_classname(),
                root_model_type = "gws.protocol.Protocol"
            )
            pt.save()

    def create_experiment(self, study: 'Study', user: 'User'=None):
        """
        Realize a protocol by creating a experiment

        :param study: The study in which the protocol is realized
        :type study: `gws.model.Study`
        :param config: The configuration of protocol
        :type config: `gws.model.Config`
        :return: The experiment
        :rtype: `gws.model.Experiment`
        """

        from .experiment import Experiment
        if user is None:
            from .service.user_service import UserService
            user = UserService.get_current_user()
            if user is None:
                raise Error("Process", "create_experiment", "A user is required")


        e = Experiment(user=user, study=study, protocol=self)

        e.save()

        return e

    def create_source_zip(self):
        graph = self.dumps()
        return zlib.compress(graph.encode())

    # -- D --

    def disconnect(self):
        """
        Disconnect the input, output, interfaces and outerfaces
        """

        super().disconnect()

        for k in self._interfaces:
            self._interfaces[k].disconnect()

        for k in self._outerfaces:
            self._outerfaces[k].disconnect()

    def dumps( self, as_dict: bool = False, prettify: bool = False, bare: bool = False ) -> str:
        """
        Dumps the JSON graph representing the protocol.

        :param as_dict: If True, returns a dictionnary. A JSON string is returns otherwise.
        :type as_dict: bool
        :param prettify: If True, the JSON string is indented.
        :type prettify: bool
        :param bare: If True, returns a bare dump i.e. the uris of the processes (and sub-protocols) of not returned. Bare dumps allow creating a new protocols from scratch.
        :type bare: bool
        """

        graph = dict(
            uri = ("" if bare else self.uri),
            nodes = {},
            links = [],
            interfaces = {},
            outerfaces = {},
        )

        for conn in self._connectors:
            link = conn.to_json(bare=bare)
            graph['links'].append(link)

        for k in self._processes:
            proc = self._processes[k]
            graph["nodes"][k] = proc.to_json(bare=bare)

        for k in self._interfaces:
            graph['interfaces'][k] = self._interfaces[k].to_json(bare=bare)

        for k in self._outerfaces:
            graph['outerfaces'][k] = self._outerfaces[k].to_json(bare=bare)

        graph["layout"] = self.get_layout()

        if as_dict:
            return graph
        else:
            if prettify:
                return json.dumps(graph, indent=4)
            else:
                return json.dumps(graph)

    # -- F --

    @classmethod
    def from_graph( cls, graph: dict ) -> 'Protocol':
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        if isinstance(graph, str):
            graph = json.loads(graph)

        if graph.get("uri"):
            proto = Protocol.get(Protocol.uri == graph.get("uri"))
        else:
            proto = Protocol()

        proto._build_from_dump(graph, rebuild=True)
        proto.data["graph"] = proto.dumps(as_dict=True)
        proto.save()

        return proto

    # -- G --

    @property
    def graph(self):
        return self.data.get("graph",{})

    def get_process(self, name: str) -> Process:
        """
        Returns a process by its name.

        :return: The process
        :rtype": Process
        """
        return self._processes[name]

    @classmethod
    def get_template(cls) -> "Protocol":
        """
        Get the template protocol
        """

        try:
            proto = cls.get( (cls.is_template == True) & (cls.type == cls.full_classname()) )
        except:
            proto = cls()
            proto.is_template = True
            proto.save()

        return proto

    def get_layout(self):
        return self.data.get("layout", {})

    def get_process_position(self, name: str):
        positions = self.get_layout()
        return positions.get(name, self._defaultPosition)

    def get_interface_of_inport(self, inport: InPort) -> Interface:
        """
        Returns interface with a given target input port

        :param inport: The InPort
        :type inport: InPort
        :return: The interface, None otherwise
        :rtype": Interface
        """

        for k in self._interfaces:
            port = self._interfaces[k].target_port
            if port is inport:
                return self._interfaces[k]

        return None

    def get_outerface_of_outport(self, outport: OutPort) -> Outerface:
        """
        Returns interface with a given target output port

        :param outport: The InPort
        :type outport: OutPort
        :return: The outerface, None otherwise
        :rtype": Outerface
        """

        for k in self._outerfaces:
            port = self._outerfacess[k].source_port
            if port is outport:
                return self._outerfacess[k]

        return None

    def get_title(self) -> str:
        """
        Get the title of the protocol

        :rtype: `str`
        """

        return self.data.get("title", "")

    def get_description(self) -> str:
        """
        Get the description of the protocol

        :rtype: `str`
        """

        return self.data.get("description", "")

    # -- I --

    @property
    def is_draft(self)->bool:
        if not self.experiment:
            return True

        return self.experiment.is_draft

    def is_child(self, process: Process) -> bool:
        """
        Returns True if the process is in the Protocol, False otherwise.

        :param process: The process
        :type process: Process
        :return: True if the process is in the Protocol, False otherwise
        :rtype: bool
        """
        return process in self._processes.values()

    def is_interfaced_with(self, process: Process) -> bool:
        """
        Returns True if the input poort the process is an interface of the protocol
        """

        for k in self._interfaces:
            port = self._interfaces[k].target_port
            if process is port.parent.parent:
                return True

        return False

    def is_outerfaced_with(self, process: Process) -> bool:
        """
        Returns True if the input poort the process is an outerface of the protocol
        """
        for k in self._outerfaces:
            port = self._outerfaces[k].source_port
            if process is port.parent.parent:
                return True

        return False

    @property
    def is_built(self):
        return bool(self._connectors)

    # -- L --

    # -- P --

    @property
    def processes(self) -> dict:
        """
        Returns the processes of the protocol

        :return: The processes as key,value dictionnary
        :rtype: `dict`
        """

        return self._processes

    # -- R --

    def _reset(self) -> bool:
        """
        Reset the protocol

        :return: Returns True if is protocol is successfully reset;  False otherwise
        :rtype: `bool`
        """

        if not super()._reset():
            return False

        for k in self._processes:
            if not self._processes[k]._reset():
                return False

        self._reset_iofaces()
        return self.save()

    def _reset_io(self):
        # > deactivated
        pass

    def _reset_iofaces(self):
        for k in self._interfaces:
            self._interfaces[k]._reset()

        for k in self._outerfaces:
            self._outerfaces[k]._reset()

    async def _run_before_task(self, *args, **kwargs):
        self.save()

        if self.is_running or self.is_finished:
            return

        self._set_inputs()

        if not self.experiment:
            raise Error("gws.model.Protocol", "_run_before_task", "No experiment defined")

        await super()._run_before_task(*args, **kwargs)

    async def task(self):
        """
        BUILT-IN PROTOCOL TASK

        Runs the process and save its state in the database.
        Override mother class method.
        """

        sources = []
        for k in self._processes:
            proc = self._processes[k]
            if proc.is_ready or self.is_interfaced_with(proc):
                sources.append(proc)

        aws = []
        for proc in sources:
            aws.append( proc._run() )

        if len(aws):
            await asyncio.gather(*aws)

    async def _run_after_task(self, *args, **kwargs):
        if self.is_finished:
            return

        # Exit the function if an inner process has not yet finished!
        for k in self._processes:
            if not self._processes[k].is_finished:
                return

        # Good! The protocol task is finished!
        self._set_outputs()
        await super()._run_after_task(*args, **kwargs)

    # -- S --

    def save(self, *args, update_graph=False, **kwargs):
        from .activity import Activity
        with self._db_manager.db.atomic() as transaction:
            for k in self._processes:
                self._processes[k].save()
            if not self.is_saved():
                Activity.add(
                    Activity.CREATE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )
            if update_graph:
                self.data["graph"] = self.dumps(as_dict=True)
            status = super().save(*args, **kwargs)
            if not status:
                transaction.rollback()
            return status


    def set_experiment(self, experiment):
        super().set_experiment(experiment)
        for k in self._processes:
            self._processes[k].set_experiment(experiment)
            self._processes[k].save()

    def set_layout(self, layout: dict):
        self.data["layout"] = layout

    def _set_inputs(self, *args, **kwargs):
        """
        Propagate resources through interfaces
        """

        for k in self._interfaces:
            port = self._interfaces[k].target_port
            port.resource = self.input[k]

    def _set_outputs(self, *args, **kwargs):
        """
        Propagate resources through outerfaces
        """

        for k in self._outerfaces:
            port = self._outerfaces[k].source_port
            self.output[k] = port.resource

    def __set_input_specs(self, input_specs):
        self.input_specs = input_specs
        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        #self.data['input_specs'] = self._input.get_specs()

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        #self.data['output_specs'] = self._output.get_specs()

    def __set_interfaces(self, interfaces: dict):
        from .service.model_service import ModelService

        input_specs = {}
        for k in interfaces:
            input_specs[k] = interfaces[k]._resource_types

        self.__set_input_specs(input_specs)

        if not self.input_specs:
            return

        self._interfaces = {}
        for k in interfaces:
            source_port = self.input.ports[k]
            self._interfaces[k] = Interface(name=k, source_port=source_port, target_port=interfaces[k])

        if self.data.get("input"):
            for k in self.data.get("input"):
                uri = self.data["input"][k]["uri"]
                type_ = self.data["input"][k]["type"]
                t = ModelService.get_model_type(type_)
                self.input.__setitem_without_check__(k, t.get(t.uri == uri) )

    def __set_outerfaces(self, outerfaces: dict):
        from .service.model_service import ModelService

        output_specs = {}
        for k in outerfaces:
            output_specs[k] = outerfaces[k]._resource_types

        self.__set_output_specs(output_specs)

        if not self.output_specs:
            return

        self._outerfaces = {}
        for k in outerfaces:
            target_port = self.output.ports[k]
            try:
                self._outerfaces[k] = Outerface(name=k, target_port=target_port, source_port=outerfaces[k])
            except:
                pass

        if self.data.get("output"):
            for k in self.data["output"]:
                uri = self.data["output"][k]["uri"]
                type_ = self.data["output"][k]["type"]
                t = ModelService.get_model_type(type_)
                self.output.__setitem_without_check__(k, t.get(t.uri == uri) )

    def set_title(self, title:str) -> str:
        """
        Set the title of the protocol

        :param title: The title
        :type title: `str`
        """

        if not isinstance(title, str):
            Error(self.full_classname(), "set_title", "The title must be a string")

        self.data["title"] = title

    def set_description(self, description:str) -> str:
        """
        Get the description of the protocol

        :param description: The description
        :type description: `str`
        """

        if not isinstance(description, str):
            Error(self.full_classname(), "set_description", "The description must be a string")

        self.data["description"] = description

    # -- T --

    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the protocol.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(shallow=shallow, **kwargs)

        if shallow:
            if _json["data"].get("graph"):
                del _json["data"]["graph"]

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

