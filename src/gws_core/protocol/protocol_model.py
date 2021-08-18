# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import zlib
from typing import Callable, Dict, List, Type, Union

from gws_core.process.process import Process
from gws_core.process.processable import Processable
from gws_core.protocol.protocol import Protocol
from peewee import BooleanField

from ..core.exception.exceptions import BadRequestException
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
from ..process.process_model import ProcessAllowedUser, ProcessModel
from ..process.processable_model import ProcessableModel
from ..resource.io import (Connector, InPort, Input, Interface, Outerface,
                           OutPort, Output)
from ..user.activity import Activity
from ..user.user import User

# TODO to remove
# Typing names generated for the class Process
CONST_PROTOCOL_TYPING_NAME = "GWS_CORE.gws_core.Protocol"


# Use the typing decorator to avoid circular dependency
@TypingDecorator(unique_name="Protocol", object_type="GWS_CORE", hide=True)
class ProtocolModel(ProcessableModel):
    """
    Protocol class.

    :property is_template: True if it is a template. False otherwise.
    A template is used to maintained a unique representation of a protocol flow in database.
    It cannot be executed and is used to efficiently instanciate new similar protocols instance.
    :type is_template: `bool`
    """

    is_template = BooleanField(default=False, index=True)

    # For lazy loading, True when processes, connectors, interfazces and outerfaces are loaded
    # True by default when creating a new protoco
    # False by default when instianting a protocol from the DB
    _is_loaded: bool = False

    _is_singleton = False
    _processes: Dict[str, ProcessableModel] = {}
    _connectors: list = []
    _interfaces: Dict[str, Interface] = {}
    _outerfaces: Dict[str, Outerface] = {}
    _table_name = "gws_protocol"  # is locked for all the protocols

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._is_loaded = self.id is None or not "graph" in self.data
        self._input = Input(self)
        self._output = Output(self)
        self._processes = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}

        # the protocol was saved in the DB
        # if self.uri and self.data.get("graph"):
        #     self.build_from_graph(self.data["graph"])

    # -- A --

    def add_process(self, name: str, process: ProcessableModel):
        """
        Adds a process to the protocol.

        :param name: Unique name of the process
        :type name: str
        :param process: The process
        :type process: Process
        """
        # be sure to have loaded the protocol before adding a process
        self._load_from_graph()
        self._add_process(name=name, process=process)

    def _add_process(self, name: str, process: ProcessableModel):
        """
        Adds a process to the protocol.

        :param name: Unique name of the process
        :type name: str
        :param process: The process
        :type process: Process
        """

        if self.is_instance_finished or self.is_instance_running:
            raise BadRequestException("The protocol has already been run")
        if not isinstance(process, ProcessableModel):
            raise BadRequestException(
                f"The process '{name}' must be an instance of ProcessableModel")
        if process.parent_protocol_id and self.id != process.parent_protocol_id:
            raise BadRequestException(
                f"The process instance '{name}' already belongs to another protocol")
        if name in self._processes:
            raise BadRequestException(f"Process name '{name}' already exists")
        if process in self._processes.items():
            raise BadRequestException(f"Process '{name}' duplicate")

        process.set_parent_protocol(self)
        if self.experiment_id:
            process.set_experiment(self.experiment)
        process.instance_name = name
        self._processes[name] = process

    def save_deep(self) -> None:
        """Save the protocol and all its processes
        """
        self.save(update_graph=True)
        self.config.save()

        for process in self.processes.values():
            process.set_parent_protocol(self)
            process.save_all()
            process.config.save()

    def add_connector(self, connector: Connector):
        """
        Adds a connector to the pfrotocol.

        :param connector: The connector
        :type connector: Connector
        """

        # Be sure to have loaded the protocol before adding a connector
        self._load_from_graph()
        self._add_connector(connector)

    def _add_connector(self, connector: Connector):
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

    def archive(self, archive: bool, archive_resources=True) -> bool:
        """
        Archive the protocol
        """

        if self.is_archived == archive:
            return True
        with self._db_manager.db.atomic() as transaction:
            for process in self.processes.values():
                if not process.archive(archive, archive_resources=archive_resources):
                    transaction.rollback()
                    return False
            status = super().archive(archive)
            if not status:
                transaction.rollback()
            return status

    # -- B --

    def _load_from_graph(self) -> None:
        if self._is_loaded:
            return
        self.build_from_graph(self.data["graph"])
        self._is_loaded = True

    def build_from_graph(self, graph: Union[str, dict], rebuild=False,
                         create_processable: Callable[[Type[Processable], str], ProcessableModel] = None) -> None:
        """
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """

        if isinstance(graph, str):
            graph = json.loads(graph)
        if not isinstance(graph, dict):
            return
        if not isinstance(graph.get("nodes"), dict) or not graph["nodes"]:
            return

        if rebuild:
            self.remove_orphan_process(graph["nodes"])

        # init processes and sub processes
        self.init_processes_from_graph(graph["nodes"], create_processable)

        # init interfaces and outerfaces
        self.init_interfaces_from_graph(graph["interfaces"])
        self.init_outerfaces_from_graph(graph["outerfaces"])

        # init connectors
        self.init_connectors_from_graph(graph["links"])

    def remove_orphan_process(self, nodes: Dict) -> None:
        """Method to remove the removed process when saving a new protocols

        :param nodes: [description]
        :type nodes: Dict
        """
        deleted_keys = []
        for key, process in self._processes.items():
            # if the process is not in the Dict or its type has changed, remove it
            if not key in nodes or process.processable_typing_name != nodes[key].get("processable_typing_name"):
                process.delete_instance()
                deleted_keys.append(key)
            # disconnect the port to prevent connection errors later
            process.disconnect()
        for key in deleted_keys:
            del self._processes[key]

    def init_processes_from_graph(self, nodes: Dict,
                                  create_processable: Callable[[Type[Processable], str], ProcessableModel] = None) -> None:
        # create nodes
        for key, node_json in nodes.items():
            proc_uri: str = node_json.get("uri", None)

            if proc_uri is None:
                raise BadRequestException(
                    f"Cannot instantiate the processable {key} because it does not have an uri")

            proc_type_str: str = node_json["processable_typing_name"]
            proc_type: Type[Processable] = TypingManager.get_type_from_name(
                proc_type_str)

            # create the processable instance
            processable: ProcessableModel
            if proc_type is None:
                raise BadRequestException(
                    f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")
            else:
                # If the processable does not exist in the DB
                if proc_uri is None:
                    if create_processable is None:
                        raise BadRequestException(
                            f"The process {key} of protocol does not have an URI.")

                    # create the processable using the create processable lambda function
                    processable = create_processable(proc_type, key)

                # If the processable exists in the DB
                else:
                    # Instantiate a process
                    if issubclass(proc_type, Process):
                        processable = ProcessModel.get_by_uri_and_check(
                            proc_uri)
                    else:
                        processable = ProtocolModel.get_by_uri_and_check(
                            proc_uri)

            self.configure_process_and_add(
                key, processable, node_json.get("config"))

    def configure_process_and_add(self, process_name: str, process: ProcessModel, config_dict: Dict) -> None:
        """Configure the process form the config dict and add the process to the process dict

        :param process_name: [description]
        :type process_name: str
        :param process: [description]
        :type process: ProcessModel
        :param config_dict: [description]
        :type config_dict: Dict
        """
        # update config if required
        if config_dict:
            params = config_dict.get("data", {}).get("params", {})
            process.config.set_params(params)

        self._add_process(process_name, process)

    def init_interfaces_from_graph(self, interfaces_dict: Dict) -> None:
        # clear current interfaces
        self._interfaces = {}

        interfaces = {}
        for key in interfaces_dict:
            # destination port of the interface
            _to: dict = interfaces_dict[key]["to"]
            proc_name: str = _to["node"]
            port_name: str = _to["port"]
            proc: ProcessableModel = self._processes[proc_name]
            port: str = proc.input.ports[port_name]
            interfaces[key] = port
        self.set_interfaces(interfaces)

    def init_outerfaces_from_graph(self, outerfaces_dict: Dict) -> None:
        # clear current interfaces
        self._outerfaces = {}

        outerfaces = {}
        for key in outerfaces_dict:
            # source port of the outerface
            _from: dict = outerfaces_dict[key]["from"]
            proc_name: str = _from["node"]
            port_name: str = _from["port"]
            proc: ProcessableModel = self._processes[proc_name]
            port: str = proc.output.ports[port_name]
            outerfaces[key] = port
        self.set_outerfaces(outerfaces)

    def init_connectors_from_graph(self, links) -> None:
        self._connectors = []
        # create links
        for link in links:
            proc_name = link["from"]["node"]
            lhs_port_name = link["from"]["port"]
            lhs_proc = self._processes[proc_name]
            proc_name = link["to"]["node"]
            rhs_port_name = link["to"]["port"]
            rhs_proc = self._processes[proc_name]

            # connector = (lhs_proc>>lhs_port_name | rhs_proc<<rhs_port_name)
            connector = (lhs_proc >> lhs_port_name).pipe(
                rhs_proc << rhs_port_name, lazy=True)
            self._add_connector(connector)

    # -- C --

    def create_source_zip(self):
        graph: str = json.dumps(self.dumps())
        return zlib.compress(graph.encode())

    # -- D --

    def disconnect(self):
        """
        Disconnect the input, output, interfaces and outerfaces
        """

        super().disconnect()
        for interface in self.interfaces.items():
            interface.disconnect()
        for outerface in self.outerfaces.items():
            outerface.disconnect()

    def dumps(self, bare: bool = False) -> str:
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
        for conn in self.connectors:
            link = conn.to_json(bare=bare)
            graph['links'].append(link)
        for key, process in self.processes.items():
            graph["nodes"][key] = process.to_json(bare=bare)
        for key, interface in self.interfaces.items():
            graph['interfaces'][key] = interface.to_json(bare=bare)
        for key, outerface in self.outerfaces.items():
            graph['outerfaces'][key] = outerface.to_json(bare=bare)
        graph["layout"] = self.get_layout()
        return graph

    # -- G --

    @property
    def graph(self):
        return self.data.get("graph", {})

    def get_process(self, name: str) -> ProcessableModel:
        """
        Returns a process by its name.

        :return: The process
        :rtype": Process
        """

        return self.processes[name]

    @classmethod
    def get_template(cls) -> "ProtocolModel":
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

        for interface in self.interfaces.values():
            port = interface.target_port
            if port is inport:
                return interface
        return None

    def get_outerface_of_outport(self, outport: OutPort) -> Outerface:
        """
        Returns interface with a given target output port

        :param outport: The InPort
        :type outport: OutPort
        :return: The outerface, None otherwise
        :rtype": Outerface
        """

        for outerface in self.outerfaces.values():
            port = outerface.source_port
            if port is outport:
                return outerface
        return None

    # -- I --

    def is_child(self, process: ProcessableModel) -> bool:
        """
        Returns True if the process is in the Protocol, False otherwise.

        :param process: The process
        :type process: Process
        :return: True if the process is in the Protocol, False otherwise
        :rtype: bool
        """

        return process in self.processes.values()

    def is_interfaced_with(self, process: ProcessableModel) -> bool:
        """
        Returns True if the input poort the process is an interface of the protocol
        """

        for interface in self.interfaces.values():
            port = interface.target_port
            if process is port.parent.parent:
                return True
        return False

    def is_outerfaced_with(self, process: ProcessableModel) -> bool:
        """
        Returns True if the input poort the process is an outerface of the protocol
        """

        for outerface in self.outerfaces.values():
            port = outerface.source_port
            if process is port.parent.parent:
                return True
        return False

    @property
    def is_built(self):
        return bool(self.connectors)

    # -- L --

    # -- P --

    @property
    def processes(self) -> Dict[str, ProcessableModel]:
        """
        Returns the processes of the protocol lazy loaded

        :return: The processes as key,value dictionnary
        :rtype: `dict`
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._processes

    @property
    def interfaces(self) -> Dict[str, Interface]:
        """
        Returns the interfaces of the protocol lazy loaded

        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._interfaces

    @property
    def outerfaces(self) -> Dict[str, Outerface]:
        """
        Returns the outerfaces of the protocol lazy loaded
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._outerfaces

    @property
    def connectors(self) -> list:
        """
        Returns the connectors of the protocol lazy loaded
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._connectors

    # -- R --

    def _reset(self) -> bool:
        """
        Reset the protocol

        :return: Returns True if is protocol is successfully reset;  False otherwise
        :rtype: `bool`
        """

        if not super()._reset():
            return False
        for process in self.processes.values():
            if not process._reset():
                return False
        self._reset_iofaces()
        return self.save()

    def _reset_io(self):
        # > deactivated
        pass

    def _reset_iofaces(self):
        for interface in self.interfaces.values():
            interface._reset()
        for outerface in self.outerfaces.values():
            outerface._reset()

    async def _run_before_task(self):
        self.save()
        if self.is_running or self.is_finished:
            return
        self._set_inputs()
        if not self.experiment:
            raise BadRequestException("No experiment defined")
        await super()._run_before_task()

    async def _run(self) -> None:
        try:
            await self._run_before_task()
            await self._run_task()
            await self._run_after_task()
        except Exception as err:
            self.progress_bar.stop(message=str(err))
            raise err

    async def _run_task(self) -> None:
        """
        BUILT-IN PROTOCOL TASK

        Runs the process and save its state in the database.
        Override mother class method.
        """

        sources: List[ProcessableModel] = []
        for process in self.processes.values():
            if process.is_ready or self.is_interfaced_with(process):
                sources.append(process)
        aws = []
        for proc in sources:
            aws.append(proc.run())
        if len(aws):
            await asyncio.gather(*aws)

    async def _run_after_task(self):
        if self.is_finished:
            return
        # Exit the function if an inner process has not yet finished!
        for k in self.processes:
            if not self.processes[k].is_finished:
                return
        # Good! The protocol task is finished!
        self._set_outputs()

        self.save(update_graph=True)
        await super()._run_after_task()

    # -- S --

    def save(self, *args, update_graph=False, **kwargs):
        with self._db_manager.db.atomic() as transaction:
            for processes in self.processes.values():
                processes.save()
            if not self.is_saved():
                Activity.add(
                    Activity.CREATE,
                    object_type=self.full_classname(),
                    object_uri=self.uri
                )
            if update_graph:
                self.data["graph"] = self.dumps()
            status = super().save(*args, **kwargs)
            if not status:
                transaction.rollback()
            return status

    def set_experiment(self, experiment):
        super().set_experiment(experiment)
        for k in self.processes:
            self.processes[k].set_experiment(experiment)
            self.processes[k].save()

    def set_layout(self, layout: dict):
        self.data["layout"] = layout

    def _set_inputs(self):
        """
        Propagate resources through interfaces
        """

        for key, interface in self.interfaces.items():
            port = interface.target_port
            port.resource = self.input[key]

    def _set_outputs(self):
        """
        Propagate resources through outerfaces
        """

        for key, outerface in self.outerfaces.items():
            port = outerface.source_port
            self.output[key] = port.resource

    def __set_input_specs(self, input_specs):
        self.input_specs = input_specs
        for k in self.input_specs:
            self._input.create_port(k, self.input_specs[k])

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k, self.output_specs[k])

    def set_interfaces(self, interfaces: dict):
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
            self._init_input()

    def set_outerfaces(self, outerfaces: dict):
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
            self._init_output()

    def set_protocol_type(self, protocol_type: Type[Protocol]) -> None:
        self.processable_typing_name = protocol_type._typing_name

    # -- T --

    def data_to_json(self, shallow=False, bare: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json = super().data_to_json(shallow=shallow, **kwargs)

        if shallow:
            if _json.get("graph"):
                del _json["graph"]

        return _json

    def check_user_privilege(self, user: User) -> None:
        """Throw an exception if the user cand execute the protocol

        :param user: user
        :type user: User
        """
        if not user.is_sysuser:
            if self._allowed_user == ProcessAllowedUser.ADMIN:
                if not user.is_admin:
                    raise UnauthorizedException(
                        "Only admin user can run protocol")
            for proc in self.processes.values():
                if proc._allowed_user == ProcessAllowedUser.ADMIN:
                    if not user.is_admin:
                        raise UnauthorizedException(
                            f"Only admin user can run process '{proc.full_classname()}'")
