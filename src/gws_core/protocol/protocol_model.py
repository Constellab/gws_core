# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
from typing import Dict, List, Type, Union

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..io.connector import Connector
from ..io.io import Inputs, Outputs
from ..io.ioface import Interface, Outerface
from ..io.port import InPort, OutPort, Port
from ..process.process_model import ProcessModel
from ..process.protocol_sub_process_builder import (
    ProtocolSubProcessBuilder, SubProcessBuilderReadFromDb)
from ..user.activity import Activity
from ..user.user import User


class ProtocolModel(ProcessModel):
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

    _processes: Dict[str, ProcessModel] = {}
    _connectors: List[Connector] = None
    _interfaces: Dict[str, Interface] = {}
    _outerfaces: Dict[str, Outerface] = {}
    _table_name = "gws_protocol"  # is locked for all the protocols

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._is_loaded = not self.is_saved() or not "graph" in self.data
        self._processes = {}
        self._interfaces = {}
        self._outerfaces = {}

    ############################### MODEL METHODS #################################

    @transaction()
    def save_full(self) -> 'ProtocolModel':
        """Save the protocol, its progress bar, its config and all its processes
        """
        self.config.save()
        # raise Exception("Bonjourrrr")
        self.progress_bar.save()
        self.save(update_graph=True)

        for process in self.processes.values():
            process.set_parent_protocol(self)
            process.save_full()

        return self

    @transaction()
    def archive(self, archive: bool, archive_resources=True) -> 'ProtocolModel':
        """
        Archive the protocol
        """

        if self.is_archived == archive:
            return self

        for process in self.processes.values():
            process.archive(archive, archive_resources=archive_resources)
        return super().archive(archive)

    def disconnect(self):
        """
        Disconnect the inputs, outputs, interfaces and outerfaces
        """

        super().disconnect()
        for interface in self.interfaces.values():
            interface.disconnect()
        for outerface in self.outerfaces.values():
            outerface.disconnect()

    @transaction()
    def reset(self) -> 'ProtocolModel':
        """
        Reset the protocol
        """

        super().reset()
        for process in self.processes.values():
            process.reset()
        self._reset_iofaces()
        return self.save(update_graph=True)

    # -- S --
    @transaction()
    def save(self, *args, update_graph=False, **kwargs) -> 'ProtocolModel':
        if not self.is_saved():
            Activity.add(
                Activity.CREATE,
                object_type=self.full_classname(),
                object_id=self.id
            )
        if update_graph:
            self.refresh_graph_from_dump()
        return super().save(*args, **kwargs)

    def set_experiment(self, experiment):
        super().set_experiment(experiment)
        for process in self.processes.values():
            process.set_experiment(experiment)

    @transaction()
    def delete_instance(self, *args, **kwargs):
        """Override delete instance to delete all the sub processes

        :return: [description]
        :rtype: [type]
        """
        for process in self.processes.values():
            process.delete_instance(recursive=True, delete_nullable=True)

        return super().delete_instance(*args, **kwargs)

    ############################### GRAPH #################################

    def _load_from_graph(self) -> None:

        if self._is_loaded:
            return

        self.build_from_graph(
            graph=self.data["graph"], sub_process_factory=SubProcessBuilderReadFromDb())
        self._is_loaded = True

    def build_from_graph(self, graph: Union[str, dict],
                         sub_process_factory: ProtocolSubProcessBuilder) -> None:
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
        self._init_processes_from_graph(graph["nodes"], sub_process_factory)

        # init interfaces and outerfaces
        self._init_interfaces_from_graph(graph["interfaces"])
        self._init_outerfaces_from_graph(graph["outerfaces"])

    def refresh_graph_from_dump(self) -> None:
        """Refresh the graph json obnject inside the data from the dump method
        """
        self.data["graph"] = self.dumps_data(minimize=True)

    # -- G --

    @property
    def graph(self):
        return self.data.get("graph", {})

    ############################### RUN #################################

    async def _run_before_task(self):
        if self.is_running or self.is_finished:
            return
        self._propagate_interfaces()
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
            self.progress_bar.stop_error(str(err))
            raise err

    async def _run_task(self) -> None:
        """
        BUILT-IN PROTOCOL TASK

        Runs the process and save its state in the database.
        Override mother class method.
        """

        sources: List[ProcessModel] = []
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
        self._propagate_outerfaces()

        await super()._run_after_task()

    def save_after_task(self) -> None:
        """Method called after the task to save the process
        """
        # override the method to update the graph before saving
        self.save(update_graph=True)

    ############################### PROCESS #################################
    @property
    def processes(self) -> Dict[str, ProcessModel]:
        """
        Returns the processes of the protocol lazy loaded

        :return: The processes as key,value dictionnary
        :rtype: `dict`
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._processes

    def add_process_model(self, process_model: ProcessModel, instance_name: str = None) -> None:
        """
        Adds a process to the protocol.

        :param process: The process
        :type process: Process
        :param instance_name: Unique name of the process. If none, the name is generated
        :type instance_name: str
        """
        # be sure to have loaded the protocol before adding a process
        self._load_from_graph()

        self._add_process_model(process_model=process_model, instance_name=instance_name)

    def _add_process_model(self, process_model: ProcessModel, instance_name: str = None) -> None:
        """
        Adds a process to the protocol.

        :param process: The process
        :type process: Process
        :param instance_name: Unique name of the process. If none, the name is generated
        :type instance_name: str
        """
        if not isinstance(process_model, ProcessModel):
            raise BadRequestException(
                f"The process '{instance_name}' must be an instance of ProcessModel")
        if process_model.parent_protocol_id and self.id != process_model.parent_protocol_id:
            raise BadRequestException(
                f"The process instance '{instance_name}' already belongs to another protocol")

        if instance_name is None:
            instance_name = self.generate_unique_instance_name(process_model.get_process_type().__name__)

        if instance_name in self._processes:
            raise BadRequestException(f"Process name '{instance_name}' already exists")
        if process_model in self._processes.items():
            raise BadRequestException(f"Process '{instance_name}' duplicate")

        process_model.set_parent_protocol(self)
        if self.experiment and process_model.experiment is None:
            process_model.set_experiment(self.experiment)

        # set instance name in process and add process
        process_model.instance_name = instance_name
        self._processes[instance_name] = process_model

    def _init_processes_from_graph(self, nodes: Dict,
                                   sub_process_factory: ProtocolSubProcessBuilder) -> None:
        # create nodes
        for key, node_json in nodes.items():

            # create the process instance
            process_model: ProcessModel = sub_process_factory.instantiate_process_from_json(
                node_json=node_json,
                instance_name=key)

            # If the process already exists
            if key in self._processes:
                # update process info
                self._processes[key].data = process_model.data
                self._processes[key].config.set_values(process_model.config.get_values())
            # If it's a new process
            else:
                self._add_process_model(process_model, key)

    def get_process(self, name: str) -> ProcessModel:
        """
        Returns a process by its name.

        :return: The process
        :rtype": Process
        """

        self._check_instance_name(name)
        return self.processes[name]

    def remove_process(self, name: str) -> None:
        self._check_instance_name(name)
        self._delete_connectors_by_process(self.processes[name])
        del self._processes[name]

    def _check_instance_name(self, instance_name: str) -> None:
        if instance_name not in self.processes:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' does not have a process named '{instance_name}'")

    ############################### CONNECTORS #################################

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
                self.init_connectors_from_graph(self.data["graph"]["links"], check_compatiblity=False)
            else:
                self._connectors = []

    def add_connector(self, connector: Connector) -> None:
        """
        Adds a connector to the pfrotocol.

        :param connector: The connector
        :type connector: Connector
        """

        # check the ports of the connector
        self._check_port(connector.in_port)
        self._check_port(connector.out_port)

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

    def _check_port(self, port: Port) -> None:
        if port.parent is None or port.parent.parent is None:
            raise Exception('The port is not linked to a process')

        process_port: ProcessModel = port.parent.parent

        if process_port.parent_protocol is None:
            raise Exception('The process is not in a protocol')

        if process_port.parent_protocol.id != self.id:
            raise Exception('The process is not a child of this protocol')

    def init_connectors_from_graph(self, links, check_compatiblity: bool = True) -> None:
        self._connectors = []
        # create links
        for link in links:
            proc_name: str = link["from"]["node"]
            lhs_port_name: str = link["from"]["port"]
            lhs_proc: ProcessModel = self._processes[proc_name]
            proc_name = link["to"]["node"]
            rhs_port_name: str = link["to"]["port"]
            rhs_proc: ProcessModel = self._processes[proc_name]

            connector: Connector = Connector(
                out_port=lhs_proc.out_port(lhs_port_name),
                in_port=rhs_proc.in_port(rhs_port_name),
                check_compatiblity=check_compatiblity)
            self._add_connector(connector)

    def _get_connectors_liked_to_process(self, process_model: ProcessModel) -> List[Connector]:
        """return the list of connectors connected to a process (input or output)
        """
        connectors: List[Connector] = []

        for connector in self.connectors:
            if connector.is_connected_to(process_model):
                connectors.append(connector)

        return connectors

    def disconnect_connectors(self) -> None:
        for connector in self.connectors:
            connector.disconnect()
        self._connectors = []

    def delete_connector(self, dest_process_name: str, dest_process_port_name: str) -> None:
        """ remove the connector which right side is connected to the specified port of the specified process
        """
        self._connectors = [
            item for item in self.connectors
            if not item.is_right_connected_to(dest_process_name, dest_process_port_name)]

    def _delete_connectors_by_process(self, process_model: ProcessModel) -> None:
        """remove all the connectors connected to a process (input or output)
        """
        self._connectors = [item for item in self.connectors if not item.is_connected_to(process_model)]

    ############################### INPUTS #################################

    @property
    def inputs(self) -> 'Inputs':
        """
        Returns inputs of the process.

        :return: The inputs
        :rtype: Inputs
        """
        if self._inputs is None:
            # load first the value if there are not loaded
            self._load_from_graph()

        return super().inputs

    ############################### OUTPUTS #################################
    @property
    def outputs(self) -> 'Outputs':
        """
        Returns outputs of the process.

        :return: The outputs
        :rtype: Outputs
        """
        if self._outputs is None:
            # load first the value if there are not loaded
            self._load_from_graph()

        return super().outputs

    ############################### INTERFACE #################################

    @property
    def interfaces(self) -> Dict[str, Interface]:
        """
        Returns the interfaces of the protocol lazy loaded

        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._interfaces

    def add_interfaces(self, interfaces: Dict[str, InPort]) -> None:
        for key, port in interfaces.items():
            self.add_interface(key, port)

    def add_interface(self, name: str,  target_port: InPort) -> None:
        self._check_port(target_port)
        # Create the input's port
        source_port: InPort = self.inputs.create_port(name, target_port.resource_spec)

        # create the interface
        self._interfaces[name] = Interface(
            name=name, source_port=source_port, target_port=target_port)

    def _propagate_interfaces(self):
        """
        Propagate resources through interfaces
        """

        for key, interface in self.interfaces.items():
            port = interface.target_port
            port.resource_model = self.inputs.get_resource_model(key)

    def is_interfaced_with(self, process: ProcessModel) -> bool:
        """
        Returns True if the input poort the process is an interface of the protocol
        """

        for interface in self.interfaces.values():
            port = interface.target_port
            if process is port.parent.parent:
                return True
        return False

    def _init_interfaces_from_graph(self, interfaces_dict: Dict) -> None:
        # clear current interfaces
        self._interfaces = {}
        self._inputs = Inputs(self)

        interfaces: Dict[str, InPort] = {}
        for key in interfaces_dict:
            # destination port of the interface
            _to: dict = interfaces_dict[key]["to"]
            proc_name: str = _to["node"]
            port_name: str = _to["port"]
            proc: ProcessModel = self._processes[proc_name]
            port: InPort = proc.inputs.ports[port_name]
            interfaces[key] = port
        self.add_interfaces(interfaces)

    def _reset_iofaces(self):
        for interface in self.interfaces.values():
            interface.reset()
        for outerface in self.outerfaces.values():
            outerface.reset()

    def remove_interface(self, name: str) -> None:
        if not name in self.interfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' does not have an interface named '{name}'")

        del self._interfaces[name]

        # delete the corresponding input's port
        self.inputs.remove_port(name)

    def port_is_interface(self, name: str, port: Port) -> bool:
        if not name in self.interfaces:
            return False

        return self.interfaces[name].target_port == port
    ############################### OUTERFACE #################################

    @property
    def outerfaces(self) -> Dict[str, Outerface]:
        """
        Returns the outerfaces of the protocol lazy loaded
        """
        # load first the value if there are not loaded
        self._load_from_graph()

        return self._outerfaces

    def _propagate_outerfaces(self):
        """
        Propagate resources through outerfaces
        """

        for key, outerface in self.outerfaces.items():
            port = outerface.source_port
            self.outputs.set_resource_model(key, port.resource_model)

    def add_outerfaces(self, outerfaces: Dict[str, OutPort]) -> None:
        for key, port in outerfaces.items():
            self.add_outerface(key, port)

    def add_outerface(self, name: str,  source_port: OutPort) -> None:
        self._check_port(source_port)

        # Create the output's port
        target_port: OutPort = self.outputs.create_port(name, source_port.resource_spec)

        # create the interface
        self._outerfaces[name] = Outerface(
            name=name, source_port=source_port, target_port=target_port)

    def is_outerfaced_with(self, process: ProcessModel) -> bool:
        """
        Returns True if the input poort the process is an outerface of the protocol
        """

        for outerface in self.outerfaces.values():
            port = outerface.source_port
            if process is port.parent.parent:
                return True
        return False

    def _init_outerfaces_from_graph(self, outerfaces_dict: Dict) -> None:
        # clear current interfaces
        self._outerfaces = {}
        self._outputs = Outputs(self)

        outerfaces: Dict[str, OutPort] = {}
        for key in outerfaces_dict:
            # source port of the outerface
            _from: dict = outerfaces_dict[key]["from"]
            proc_name: str = _from["node"]
            port_name: str = _from["port"]
            proc: ProcessModel = self._processes[proc_name]
            port: OutPort = proc.outputs.ports[port_name]
            outerfaces[key] = port
        self.add_outerfaces(outerfaces)

    def remove_outerface(self, name: str) -> None:
        if not name in self._outerfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' does not have an outerface named '{name}'")

        del self._outerfaces[name]

        # delete the corresponding output
        self.outputs.remove_port(name)

    ############################### JSON #################################

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
        for key, process in self.processes.items():
            process_json: dict
            if minimize:
                process_json = process.get_minimum_json()
            else:
                process_json = process.to_json(deep=False)
            graph["nodes"][key] = process_json
        for key, interface in self.interfaces.items():
            graph['interfaces'][key] = interface.to_json()
        for key, outerface in self.outerfaces.items():
            graph['outerfaces'][key] = outerface.to_json()
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

    def export_config(self) -> Dict:

        _json = super().export_config()

        graph = {
            "nodes": {},
            "links": [],
            "interfaces": {},
            "outerfaces": {}
        }

        for conn in self.connectors:
            graph['links'].append(conn.export_config())
        for key, process in self.processes.items():
            graph["nodes"][key] = process.export_config()
        for key, interface in self.interfaces.items():
            graph['interfaces'][key] = interface.export_config()
        for key, outerface in self.outerfaces.items():
            graph['outerfaces'][key] = outerface.export_config()
        _json["graph"] = graph
        return _json

    ############################### OTHER #################################

    def is_protocol(self) -> bool:
        return True

    @property
    def is_built(self):
        return bool(self.connectors)

    def check_user_privilege(self, user: User) -> None:
        """Throw an exception if the user cand execute the protocol

        :param user: user
        :type user: User
        """

        super().check_user_privilege(user)

        for proc in self.processes.values():
            proc.check_user_privilege(user)

    def generate_unique_instance_name(self, instance_name: str) -> str:
        """ Generate a unique instance name from an instance_name
        by adding _1 or _2... to the end of the instance name
        """
        if not instance_name in self.processes:
            return instance_name

        count: int = 1
        while f"{instance_name}_{count}" in self.processes:
            count += 1

        return f"{instance_name}_{count}"

    def get_protocol_chain_info(self) -> str:
        """return a string with the information up to the main protocol
        """

        if self.parent_protocol_id is None:
            return "Main protocol"

        return f"{self.parent_protocol.get_protocol_chain_info()} > {self.instance_name}"
