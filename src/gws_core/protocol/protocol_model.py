# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import zlib
from typing import Dict, List, Type, Union

from ..core.decorator.transaction import Transaction
from ..core.exception.exceptions import BadRequestException
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..io.connector import Connector
from ..io.io import Input, Output
from ..io.ioface import Interface, Outerface
from ..io.port import InPort, OutPort, Port
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
from ..process.process_model import ProcessAllowedUser, ProcessModel
from ..process.processable import Processable
from ..process.processable_model import ProcessableModel
from ..protocol.protocol import Protocol
from ..resource.resource import Resource
from ..user.activity import Activity
from ..user.user import User
from .sub_processable_factory import (SubProcessableFactory,
                                      SubProcessFactoryReadFromDb)


@TypingDecorator(unique_name="Protocol", object_type="GWS_CORE", hide=True)
class ProtocolModel(ProcessableModel):
    """
    Protocol class.

    :property is_template: True if it is a template. False otherwise.
    A template is used to maintained a unique representation of a protocol flow in database.
    It cannot be executed and is used to efficiently instanciate new similar protocols instance.
    :type is_template: `bool`
    """

    # For lazy loading, True when processes, connectors, interfazces and outerfaces are loaded
    # True by default when creating a new protoco
    # False by default when instianting a protocol from the DB
    _is_loaded: bool = False

    _is_singleton = False
    _processes: Dict[str, ProcessableModel] = {}
    _connectors: List[Connector] = []
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

    @Transaction()
    def save_full(self) -> None:
        """Save the protocol, its progress bar, its config and all its processes
        """
        self.config.save()
        # raise Exception("Bonjourrrr")
        self.progress_bar.save()
        self.save(update_graph=True)

        for process in self.processes.values():
            process.set_parent_protocol(self)
            process.save_full()

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
            raise BadRequestException("Duplicated connector")
        self._connectors.append(connector)

    @Transaction()
    def archive(self, archive: bool, archive_resources=True) -> 'ProtocolModel':
        """
        Archive the protocol
        """

        if self.is_archived == archive:
            return self

        for process in self.processes.values():
            process.archive(archive, archive_resources=archive_resources)
        return super().archive(archive)

    # -- B --

    def _load_from_graph(self) -> None:

        if self._is_loaded:
            return

        self.build_from_graph(
            graph=self.data["graph"], sub_processable_factory=SubProcessFactoryReadFromDb())
        self._is_loaded = True

    def build_from_graph(self, graph: Union[str, dict],
                         sub_processable_factory: SubProcessableFactory) -> None:
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

        # init processes and sub processes
        self.init_processes_from_graph(graph["nodes"], sub_processable_factory)

        # init interfaces and outerfaces
        self.init_interfaces_from_graph(graph["interfaces"])
        self.init_outerfaces_from_graph(graph["outerfaces"])

        # init connectors
        self.init_connectors_from_graph(graph["links"])

    def init_processes_from_graph(self, nodes: Dict,
                                  sub_processable_factory: SubProcessableFactory) -> None:
        # create nodes
        for key, node_json in nodes.items():
            proc_uri: str = node_json.get("uri", None)

            proc_type_str: str = node_json["processable_typing_name"]
            proc_type: Type[Processable] = TypingManager.get_type_from_name(
                proc_type_str)

            if proc_type is None:
                raise BadRequestException(
                    f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")

            # create the processable instance
            processable: ProcessableModel = sub_processable_factory.instantiate_processable(processable_uri=proc_uri,
                                                                                            processable_type=proc_type,
                                                                                            instance_name=key)

            if key in self._processes:
                self._processes[key].data = processable.data
            else:
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

        interfaces: Dict[str, Port] = {}
        for key in interfaces_dict:
            # destination port of the interface
            _to: dict = interfaces_dict[key]["to"]
            proc_name: str = _to["node"]
            port_name: str = _to["port"]
            proc: ProcessableModel = self._processes[proc_name]
            port: Port = proc.input.ports[port_name]
            interfaces[key] = port
        self.set_interfaces(interfaces)

    def init_outerfaces_from_graph(self, outerfaces_dict: Dict) -> None:
        # clear current interfaces
        self._outerfaces = {}

        outerfaces: Dict[str, Port] = {}
        for key in outerfaces_dict:
            # source port of the outerface
            _from: dict = outerfaces_dict[key]["from"]
            proc_name: str = _from["node"]
            port_name: str = _from["port"]
            proc: ProcessableModel = self._processes[proc_name]
            port: Port = proc.output.ports[port_name]
            outerfaces[key] = port
        self.set_outerfaces(outerfaces)

    def init_connectors_from_graph(self, links) -> None:
        self._connectors = []
        # create links
        for link in links:
            proc_name: str = link["from"]["node"]
            lhs_port_name: str = link["from"]["port"]
            lhs_proc: ProcessableModel = self._processes[proc_name]
            proc_name = link["to"]["node"]
            rhs_port_name: str = link["to"]["port"]
            rhs_proc: ProcessableModel = self._processes[proc_name]

            # connector = (lhs_proc>>lhs_port_name | rhs_proc<<rhs_port_name)
            connector: Connector = (lhs_proc >> lhs_port_name).pipe(
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
        for interface in self.interfaces.values():
            interface.disconnect()
        for outerface in self.outerfaces.values():
            outerface.disconnect()

    def dumps(self) -> dict:
        """
        Dumps the JSON graph representing the protocol.

        """

        graph = dict(
            uri=self.uri,
            nodes={},
            links=[],
            interfaces={},
            outerfaces={},
        )
        for conn in self.connectors:
            link = conn.to_json()
            graph['links'].append(link)
        for key, process in self.processes.items():
            graph["nodes"][key] = process.to_json(deep=True)
        for key, interface in self.interfaces.items():
            graph['interfaces'][key] = interface.to_json()
        for key, outerface in self.outerfaces.items():
            graph['outerfaces'][key] = outerface.to_json()
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
    def connectors(self) -> List[Connector]:
        """
        Returns the connectors of the protocol lazy loaded
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._connectors

    @property
    def input(self) -> 'Input':
        """
        Returns input of the process.

        :return: The input
        :rtype: Input
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return super().input

    @property
    def output(self) -> 'Output':
        """
        Returns input of the process.

        :return: The input
        :rtype: Input
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return super().output

    # -- R --

    @Transaction()
    def reset(self) -> 'ProtocolModel':
        """
        Reset the protocol

        :return: Returns True if is protocol is successfully reset;  False otherwise
        :rtype: `bool`
        """

        super().reset()
        for process in self.processes.values():
            process.reset()
        self._reset_iofaces()
        return self.save()

    def _reset_io(self):
        # > deactivated
        pass

    def _reset_iofaces(self):
        for interface in self.interfaces.values():
            interface.reset()
        for outerface in self.outerfaces.values():
            outerface.reset()

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
        # TODO est-ce qu'il faut mettre à jour la progress bar ?
        for proc in sources:
            aws.append(proc.run())
        if len(aws):
            await asyncio.gather(*aws)

    async def _run_after_task(self):
        if self.is_finished:
            return
        # Exit the function if an inner process has not yet finished!
        for process in self.processes.values():
            if not process.is_finished:
                return
        # Good! The protocol task is finished!
        self._set_outputs()

        self.save(update_graph=True)
        await super()._run_after_task()

    # -- S --
    @Transaction()
    def save(self, *args, update_graph=False, **kwargs) -> 'ProtocolModel':
        if not self.is_saved():
            Activity.add(
                Activity.CREATE,
                object_type=self.full_classname(),
                object_uri=self.uri
            )
        if update_graph:
            self.data["graph"] = self.dumps()
        return super().save(*args, **kwargs)

    def set_experiment(self, experiment):
        super().set_experiment(experiment)
        for process in self.processes.values():
            process.set_experiment(experiment)
            process.save()

    def set_layout(self, layout: dict):
        self.data["layout"] = layout

    def _set_inputs(self):
        """
        Propagate resources through interfaces
        """

        for key, interface in self.interfaces.items():
            port = interface.target_port
            port.resource_model = self.input[key]

    def _set_outputs(self):
        """
        Propagate resources through outerfaces
        """

        for key, outerface in self.outerfaces.items():
            port = outerface.source_port
            self.output[key] = port.resource_model

    def __set_input_specs(self, input_specs: Dict[str, Type[Resource]]):
        for key, spec in input_specs.items():
            self._input.create_port(key, spec)

    def __set_output_specs(self, output_specs: Dict[str, Type[Resource]]):
        for key, spec in output_specs.items():
            self._output.create_port(key, spec)

    def set_interfaces(self, interfaces: Dict[str, Port]):
        input_specs = {}
        for k in interfaces:
            input_specs[k] = interfaces[k].resource_types
        if not input_specs:
            return
        self.__set_input_specs(input_specs)
        self._interfaces = {}
        for k in interfaces:
            source_port = self._input.ports[k]
            self._interfaces[k] = Interface(
                name=k, source_port=source_port, target_port=interfaces[k])
        if self.data.get("input"):
            self._init_input()

    def set_outerfaces(self, outerfaces: Dict[str, Port]):
        output_specs = {}
        for k in outerfaces:
            output_specs[k] = outerfaces[k].resource_types
        if not output_specs:
            return
        self.__set_output_specs(output_specs)
        self._outerfaces = {}
        for k in outerfaces:
            target_port = self._output.ports[k]
            try:
                self._outerfaces[k] = Outerface(
                    name=k, target_port=target_port, source_port=outerfaces[k])
            except:
                pass
        if self.data.get("output"):
            self._init_output()

    def set_protocol_type(self, protocol_type: Type[Protocol]) -> None:
        self.processable_typing_name = protocol_type._typing_name

    def delete_process(self, instance_name: str) -> None:
        if not instance_name in self.processes:
            raise BadRequestException(
                f"The process with instance_name {instance_name} does not exist ")

        self.processes[instance_name].delete_instance()
        del self.processes[instance_name]

    # -- T --

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json = super().data_to_json(deep=deep, **kwargs)

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
