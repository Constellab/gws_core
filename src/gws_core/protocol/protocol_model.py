# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
from typing import Dict, List, Type, Union

from ..core.decorator.transaction import Transaction
from ..core.exception.exceptions import BadRequestException
from ..io.connector import Connector
from ..io.io import Input, Output
from ..io.ioface import Interface, Outerface
from ..io.port import InPort, OutPort, Port
from ..model.typing_register_decorator import TypingDecorator
from ..processable.processable_model import ProcessableModel
from ..processable.sub_processable_factory import (SubProcessableFactory,
                                                   SubProcessFactoryReadFromDb)
from ..protocol.protocol import Protocol
from ..resource.resource import Resource
from ..user.activity import Activity
from ..user.user import User


@TypingDecorator(unique_name="Protocol", object_type="GWS_CORE", hide=True)
class ProtocolModel(ProcessableModel):
    """
    Protocol class.

    :property is_template: True if it is a template. False otherwise.
    A template is used to maintained a unique representation of a protocol flow in database.
    It cannot be executed and is used to efficiently instanciate new similar protocols instance.
    :type is_template: `bool`
    """

    # For lazy loading, True when processes, interfazces and outerfaces are loaded
    # True by default when creating a new protoco
    # False by default when instianting a protocol from the DB
    _is_loaded: bool = False

    _processes: Dict[str, ProcessableModel] = {}
    _connectors: List[Connector] = None
    _interfaces: Dict[str, Interface] = {}
    _outerfaces: Dict[str, Outerface] = {}
    _table_name = "gws_protocol"  # is locked for all the protocols

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._is_loaded = self.id is None or not "graph" in self.data
        self._input = Input(self)
        self._output = Output(self)
        self._processes = {}
        self._interfaces = {}
        self._outerfaces = {}

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
        if self.experiment and process.experiment is None:
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
        self._load_connectors()
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
        self._init_processes_from_graph(graph["nodes"], sub_processable_factory)

        # init interfaces and outerfaces
        self._init_interfaces_from_graph(graph["interfaces"])
        self._init_outerfaces_from_graph(graph["outerfaces"])

    def _init_processes_from_graph(self, nodes: Dict,
                                   sub_processable_factory: SubProcessableFactory) -> None:
        # create nodes
        for key, node_json in nodes.items():

            # create the processable instance
            processable: ProcessableModel = sub_processable_factory.instantiate_processable_from_json(
                node_json=node_json,
                instance_name=key)

            # If the process already exists
            if key in self._processes:
                # update process info
                self._processes[key].data = processable.data
                self._processes[key].config.set_params(processable.config.params)
            # If it's a new process
            else:
                self._add_process(key, processable)

    def _init_interfaces_from_graph(self, interfaces_dict: Dict) -> None:
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

    def _init_outerfaces_from_graph(self, outerfaces_dict: Dict) -> None:
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

            connector: Connector = Connector(out_port=lhs_proc.out_port(lhs_port_name),
                                             in_port=rhs_proc.in_port(rhs_port_name), check_compatiblity=True)
            self._add_connector(connector)

    # -- C --

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

    def refresh_graph_from_dump(self) -> None:
        """Refresh the graph json obnject inside the data from the dump method
        """
        self.data["graph"] = self.dumps_data(minimize=True)

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

        # Lazy load specifically the connector because it might need to load the children (for sub protocol)
        self._load_connectors()

        return self._connectors

    def _load_connectors(self) -> None:
        if self._connectors is None:
            # Init the connector from the graph
            if "graph" in self.data and "links" in self.data["graph"]:
                self.init_connectors_from_graph(self.data["graph"]["links"])
            else:
                self._connectors = []

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
        if self.is_running or self.is_finished:
            return
        self._set_inputs()
        if not self.experiment:
            raise BadRequestException("No experiment defined")
        await super()._run_before_task()

    async def _run(self) -> None:
        # completely load the protocol before running it
        self._load_from_graph()
        self._load_connectors()

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

        await super()._run_after_task()

    def save_after_task(self) -> None:
        """Method called after the task to save the processable
        """
        # override the method to update the graph before saving
        self.save(update_graph=True)

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
            self.refresh_graph_from_dump()
        return super().save(*args, **kwargs)

    def set_experiment(self, experiment):
        super().set_experiment(experiment)
        for process in self.processes.values():
            process.set_experiment(experiment)

    def set_layout(self, layout: dict):
        self.data["layout"] = layout

    def _set_inputs(self):
        """
        Propagate resources through interfaces
        """

        for key, interface in self.interfaces.items():
            port = interface.target_port
            port.resource_model = self.input.get_resource_model(key)

    def _set_outputs(self):
        """
        Propagate resources through outerfaces
        """

        for key, outerface in self.outerfaces.items():
            port = outerface.source_port
            self.output.set_resource_model(key, port.resource_model)

    def __set_input_specs(self, input_specs: Dict[str, Type[Resource]]):
        for key, spec in input_specs.items():
            self._input.create_port(key, spec)

    def __set_output_specs(self, output_specs: Dict[str, Type[Resource]]):
        for key, spec in output_specs.items():
            self._output.create_port(key, spec)

    def set_interfaces(self, interfaces: Dict[str, Port]):
        input_specs = {}
        for key in interfaces:
            input_specs[key] = interfaces[key].resource_types
        if not input_specs:
            return
        self.__set_input_specs(input_specs)
        self._interfaces = {}
        for key in interfaces:
            source_port = self._input.get_port(key)
            self._interfaces[key] = Interface(
                name=key, source_port=source_port, target_port=interfaces[key])

        self._init_input_from_data()

    def set_outerfaces(self, outerfaces: Dict[str, Port]):
        output_specs = {}
        for key in outerfaces:
            output_specs[key] = outerfaces[key].resource_types
        if not output_specs:
            return
        self.__set_output_specs(output_specs)
        self._outerfaces = {}
        for key in outerfaces:
            target_port = self._output.get_port(key)
            self._outerfaces[key] = Outerface(
                name=key, target_port=target_port, source_port=outerfaces[key])

        self._init_output_from_data()

    def set_protocol_type(self, protocol_type: Type[Protocol]) -> None:
        self.processable_typing_name = protocol_type._typing_name

    def delete_process(self, instance_name: str) -> None:
        if not instance_name in self.processes:
            raise BadRequestException(
                f"The process with instance_name {instance_name} does not exist ")

        self.processes[instance_name].delete_instance()
        del self.processes[instance_name]

    def is_protocol(self) -> bool:
        return True

    def dumps_data(self, minimize: bool) -> dict:
        """
        Dumps the JSON graph representing the protocol.

        """

        graph = {
            "nodes": {},
            "links": [],
            "interfaces": {},
            "outerfaces": {}
        }

        for conn in self.connectors:
            link = conn.to_json()
            graph['links'].append(link)
        for key, processable in self.processes.items():
            processable_json: dict
            if minimize:
                processable_json = processable.get_minimum_json()
            else:
                processable_json = processable.to_json(deep=False)
            graph["nodes"][key] = processable_json
        for key, interface in self.interfaces.items():
            graph['interfaces'][key] = interface.to_json()
        for key, outerface in self.outerfaces.items():
            graph['outerfaces'][key] = outerface.to_json()
        graph["layout"] = self.get_layout()
        return graph

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json: dict = super().data_to_json(deep=deep)

        if deep:
            _json["graph"] = self.dumps_data(minimize=False)

        return _json

    def check_user_privilege(self, user: User) -> None:
        """Throw an exception if the user cand execute the protocol

        :param user: user
        :type user: User
        """

        super().check_user_privilege(user)

        for proc in self.processes.values():
            proc.check_user_privilege(user)
