# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import zlib
from typing import Union

from gws_core.model.typing_register_decorator import TypingDecorator
from peewee import BooleanField

from ..core.exception.exceptions import BadRequestException
from ..model.typing_manager import TypingManager
from ..process.process import Process
from ..resource.io import (Connector, InPort, Input, Interface, Outerface,
                           OutPort, Output)
from ..user.activity import Activity
from ..user.current_user_service import CurrentUserService
from ..user.user import User

# Typing names generated for the class Process
CONST_PROTOCOL_TYPING_NAME = "PROTOCOL.gws_core.Protocol"

# Use the typing decorator to avoid circular dependency


@TypingDecorator(name_unique="Protocol", object_type="PROTOCOL", hide=True)
class Protocol(Process):
    """
    Protocol class.

    :property is_template: True if it is a template. False otherwise.
    A template is used to maintained a unique representation of a protocol flow in database.
    It cannot be executed and is used to efficiently instanciate new similar protocols instance.
    :type is_template: `bool`
    """

    is_template = BooleanField(default=False, index=True)

    _is_singleton = False
    _processes: dict = {}
    _connectors: list = []
    _interfaces: dict = {}
    _outerfaces: dict = {}
    _table_name = "gws_protocol"  # is locked for all the protocols

    def __init__(self, *args,
                 processes: dict = None,
                 connectors: list = None,
                 interfaces: dict = None,
                 outerfaces: dict = None,
                 user=None, **kwargs):

        super().__init__(*args, user=user, **kwargs)
        self._input = Input(self)
        self._output = Output(self)
        self._processes = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}

        # the protocol was saved in the super-class
        if self.uri and self.data.get("graph"):
            self._build_from_dump(self.data["graph"])
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
            raise BadRequestException("The protocol has already been run")
        if not isinstance(process, Process):
            raise BadRequestException(
                "The process '{name}' must be an instance of Process")
        if process.protocol_id and self.id != process.protocol_id:
            raise BadRequestException(
                "The process instance '{name}' already belongs to another protocol")
        if name in self._processes:
            raise BadRequestException("Process name '{name}' already exists")
        if process in self._processes.items():
            raise BadRequestException("Process '{name}' duplicate")

        process.set_protocol(self)
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
            raise BadRequestException("The protocol has already been run")
        if not isinstance(connector, Connector):
            raise BadRequestException(
                "The connector must be an instance of Connector")
        if not connector.left_process in self._processes.values() or \
                not connector.right_process in self._processes.values():
            raise BadRequestException(
                "The processes of the connector must belong to the protocol")
        if connector in self._connectors:
            raise BadRequestException("Duplciated connector")
        self._connectors.append(connector)

    def archive(self, tf: bool, archive_resources=True) -> bool:
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

    def _build(self, processes: dict = None, connectors: list = None, interfaces: dict = None, outerfaces: dict = None, user=None, **kwargs):
        if processes is None:
            processes = {}
        if connectors is None:
            connectors = []
        if interfaces is None:
            interfaces = {}
        if outerfaces is None:
            outerfaces = {}
        if not isinstance(processes, dict):
            raise BadRequestException("A dictionnary of processes is expected")
        if not isinstance(connectors, list):
            raise BadRequestException("A list of connectors is expected")

        # set process
        for name in processes:
            proc = processes[name]
            if not isinstance(proc, Process):
                raise BadRequestException(
                    "The dictionnary of processes must contain instances of Process")
            self.add_process(name, proc)

        # set connectors
        for conn in connectors:
            if not isinstance(conn, Connector):
                raise BadRequestException(
                    "The list of connector must contain instances of Connectors")
            self.add_connector(conn)

        if user is None:
            try:
                user = CurrentUserService.get_and_check_current_user()
            except Exception as err:
                raise BadRequestException("A user is required") from err

        if isinstance(user, User):
            if self.created_by.is_sysuser:
                # The sysuser is used by default to create any Process
                # We therefore replace the syssuser by the currently authenticated user
                if user.is_authenticated:
                    self.create_by = user
                else:
                    raise BadRequestException("The user must be authenticated")
        else:
            raise BadRequestException("The user must be an instance of User")

        # set interfaces
        self.__set_interfaces(interfaces)
        self.__set_outerfaces(outerfaces)
        self.data["graph"] = self.dumps(as_dict=True)
        self.save()  # <- will save the graph

    def _build_from_dump(self, graph: Union[str, dict], rebuild=False) -> 'Protocol':
        """
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """

        # Do not build the protocol if it is not draft and is already built
        if self.is_built and not self.is_draft:
            return True

        if isinstance(graph, str):
            graph = json.loads(graph)
        if not isinstance(graph, dict):
            return
        if not isinstance(graph.get("nodes"), dict) or not graph["nodes"]:
            return

        if rebuild and self.is_draft:
            deleted_keys = []
            for k in self._processes:
                proc = self._processes[k]
                is_removed = False
                if k in graph["nodes"]:
                    if proc.typing_name != graph["nodes"][k].get("typing_name"):
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
            proc_uri = node_json.get("uri", None)
            proc_type_str = node_json["typing_name"]
            proc_t = TypingManager.get_type_from_name(proc_type_str)
            if proc_t is None:
                raise BadRequestException(
                    f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")
            else:
                if proc_uri:
                    proc = proc_t.get(proc_t.uri == proc_uri)
                else:
                    if issubclass(proc_t, Protocol):
                        proc = Protocol.from_graph(
                            node_json["data"]["graph"])
                    else:
                        proc = proc_t()
                if k in self._processes:
                    # copy current data
                    self._processes[k].data = proc.data
                else:
                    self.add_process(k, proc)

            # update config if required
            config_json = node_json.get("config")
            if config_json:
                params = config_json.get("data", {}).get("params", {})
                if k in self._processes:
                    self._processes[k].config.set_params(params)
                else:
                    proc.config.set_params(params)
                proc.config.save()
                proc.save()

        # create interfaces and outerfaces
        interfaces = {}
        outerfaces = {}
        for k in graph["interfaces"]:
            # destination port of the interface
            _to = graph["interfaces"][k]["to"]
            proc_name = _to["node"]
            port_name = _to["port"]
            proc = self._processes[proc_name]
            port = proc.input.ports[port_name]
            interfaces[k] = port
        for k in graph["outerfaces"]:
            # source port of the outerface
            _from = graph["outerfaces"][k]["from"]
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
            connector = (lhs_proc >> lhs_port_name).pipe(
                rhs_proc << rhs_port_name, lazy=True)
            self.add_connector(connector)
        self.save(update_graph=True)

    # -- C --

    @classmethod
    def create_table(cls, *args, **kwargs):
        """
        Create model table
        """

        if cls._table_name != Protocol._table_name:
            raise BadRequestException(
                f"The table name of {cls.full_classname()} must be {Protocol._table_name}")
        kwargs["check_table_name"] = False
        super().create_table(*args, **kwargs)

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

    def dumps(self, as_dict: bool = False, prettify: bool = False, bare: bool = False) -> str:
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
            uri=("" if bare else self.uri),
            nodes={},
            links=[],
            interfaces={},
            outerfaces={},
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
        if prettify:
            return json.dumps(graph, indent=4)
        else:
            return json.dumps(graph)

    # -- F --

    @classmethod
    def from_graph(cls, graph: dict) -> 'Protocol':
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
        return self.data.get("graph", {})

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
        # todo fix type
        try:
            proto = cls.get((cls.is_template == True) & (
                cls.type == cls.full_classname()))
        except:
            proto = cls()
            proto.is_template = True
            proto.save()
        return proto

    def get_layout(self):
        return self.data.get("layout", {})

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
    def is_draft(self) -> bool:
        if not self.experiment:
            return True
        from ..experiment.experiment import ExperimentStatus
        return self.experiment.status == ExperimentStatus.DRAFT

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
            raise BadRequestException("No experiment defined")
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
            aws.append(proc._run())
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
        with self._db_manager.db.atomic() as transaction:
            for processes in self._processes.values():
                processes.save()
            if not self.is_saved():
                Activity.add(
                    Activity.CREATE,
                    object_type=self.full_classname(),
                    object_uri=self.uri
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
            self._input.create_port(k, self.input_specs[k])

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k, self.output_specs[k])

    def __set_interfaces(self, interfaces: dict):
        input_specs = {}
        for k in interfaces:
            input_specs[k] = interfaces[k]._resource_types
        self.__set_input_specs(input_specs)
        if not self.input_specs:
            return
        self._interfaces = {}
        for k in interfaces:
            source_port = self.input.ports[k]
            self._interfaces[k] = Interface(
                name=k, source_port=source_port, target_port=interfaces[k])
        if self.data.get("input"):
            for k in self.data.get("input"):
                model = TypingManager.get_object_with_typing_name_and_uri(
                    self.data["input"][k]["typing_name"],  self.data["input"][k]["uri"])
                self.input.__setitem_without_check__(k, model)

    def __set_outerfaces(self, outerfaces: dict):
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
                self._outerfaces[k] = Outerface(
                    name=k, target_port=target_port, source_port=outerfaces[k])
            except:
                pass
        if self.data.get("output"):
            for k in self.data["output"]:
                model = TypingManager.get_object_with_typing_name_and_uri(
                    self.data["output"][k]["typing_name"], self.data["output"][k]["uri"])
                self.output.__setitem_without_check__(k, model)

    def set_title(self, title: str) -> str:
        """
        Set the title of the protocol

        :param title: The title
        :type title: `str`
        """

        if not isinstance(title, str):
            raise BadRequestException("The title must be a string")
        self.data["title"] = title

    def set_description(self, description: str) -> str:
        """
        Get the description of the protocol

        :param description: The description
        :type description: `str`
        """

        if not isinstance(description, str):
            raise BadRequestException("The description must be a string")
        self.data["description"] = description

    # -- T --

    def to_json(self, *, shallow=False, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[str, dict]:
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

    def check_user_privilege(self, user: User) -> None:
        """Throw an exception if the user cand execute the protocol

        :param user: user
        :type user: User
        """
        if not user.is_sysuser:
            if self._allowed_user == self.USER_ADMIN:
                if not user.is_admin:
                    raise BadRequestException(
                        "Only admin user can run protocol")
            for proc in self.processes.values():
                if proc._allowed_user == self.USER_ADMIN:
                    if not user.is_admin:
                        raise BadRequestException(
                            f"Only admin user can run process '{proc.full_classname()}'")
