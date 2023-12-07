# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Literal, Optional, Set

from gws_core.core.utils.date_helper import DateHelper
from gws_core.protocol.protocol_spec import ConnectorSpec, InterfaceSpec
from gws_core.protocol.protocol_types import ConnectorDict

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.model.db_field import SerializableDBField
from ..io.connector import Connector
from ..io.io import Inputs, Outputs
from ..io.ioface import Interface, Outerface
from ..io.port import InPort, OutPort, Port
from ..process.process_model import ProcessModel
from ..process.process_types import ProcessStatus
from ..process.protocol_sub_process_builder import (
    ProtocolSubProcessBuilder, SubProcessBuilderReadFromDb)
from ..user.user import User
from .protocol_layout import ProtocolLayout


class ProtocolModel(ProcessModel):

    layout: ProtocolLayout = SerializableDBField(
        object_type=ProtocolLayout, null=True)

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
        self._is_loaded = not self.is_saved() or not self.data or not "graph" in self.data
        self._processes = {}
        self._interfaces = {}
        self._outerfaces = {}

    ############################### MODEL METHODS #################################

    @transaction()
    def save_full(self) -> 'ProtocolModel':
        """Save the protocol, its progress bar, its config and all its processes
        """
        self.config.save()
        self.progress_bar.save()
        self.save_graph()

        for process in self.processes.values():
            process.set_parent_protocol(self)
            process.save_full()

        return self

    @transaction()
    def archive(self, archive: bool) -> 'ProtocolModel':
        """
        Archive the protocol
        """

        if self.is_archived == archive:
            return self

        for process in self.processes.values():
            process.archive(archive)
        return super().archive(archive)

    @transaction()
    def reset(self) -> 'ProtocolModel':
        """
        Reset the protocol
        """

        super().reset()
        for process in self.processes.values():
            process.reset()
        self._reset_iofaces()

        # auto execute the source task
        for process in self.processes.values():
            if process.is_source_task():
                process.run()

        # re-propagate the resources (because source task has been executed)
        # and save processes
        self.propagate_resources()

        return self.save_graph()

    def save_graph(self) -> 'ProtocolModel':
        self.refresh_graph_from_dump()
        return self.save()

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

    def build_from_graph(self, graph: dict,
                         sub_process_factory: ProtocolSubProcessBuilder) -> None:
        """
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """
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
        self.data["graph"] = self.dumps_graph(process_mode='minimize')

    @property
    def graph(self):
        return self.data.get("graph", {})

    ############################### RUN #################################

    def _run_before_task(self):
        if self.is_running or self.is_finished:
            return
        self._propagate_interfaces()
        if not self.experiment:
            raise BadRequestException("No experiment defined")
        super()._run_before_task()

    def _run(self) -> None:
        # completely load the protocol before running it
        self._load_from_graph()
        self._load_connectors()

        self._run_before_task()
        self._run_protocol()
        self._run_after_task()

    def run_process(self, process_instance_name: str) -> None:
        """ Method to run a single process of the protocol

        :param process_instance_name: process to run
        :type process_instance_name: str
        """

        # completely load the protocol before running it
        self._load_from_graph()
        self._load_connectors()

        process = self.get_process(process_instance_name)
        if process.is_success:
            raise BadRequestException("The process is already finished")

        if process.is_error:
            process.reset()

        if not self.process_is_ready(process):
            raise BadRequestException(
                "The process cannot be run because it is not ready. Where the previous process run and are the inputs provided ?")

        self._run_before_task()
        self.mark_as_started()
        self._run_process(process)
        self._run_after_task()

    def _run_protocol(self) -> None:
        """
        BUILT-IN PROTOCOL TASK

        Runs the process and save its state in the database.
        Override mother class method.
        """
        # create a dictionaly of runned processes with the instance name as key
        runned_processes = {
            key: process for key, process in self.processes.items() if process.is_finished}

        count_processes = len(self.processes)

        while len(runned_processes) < count_processes:

            has_runned = False
            for process in self.processes.values():

                if process.instance_name not in runned_processes and self.process_is_ready(process):
                    has_runned = True
                    self._run_process(process)

                    runned_processes[process.instance_name] = process
                    self.progress_bar.update_progress(round(len(runned_processes) / count_processes * 100),
                                                      f"Process finished {process.get_name()}")

            # if no process has been runned, it means that the protocol is finished
            if not has_runned:
                break

        if len(runned_processes) < count_processes:
            self.progress_bar.add_warning_message(
                "Some processes are not ready to be runned")

    def _run_process(self, process: ProcessModel) -> None:
        self.progress_bar.add_info_message(
            f"Run process {process.get_name()}")
        process.run()

        # propagate the outputs of the process to all the connected inputs
        next_processes: Dict[str, ProcessModel] = {}
        for connector in self.connectors:
            if connector.left_process.instance_name == process.instance_name:
                connector.propagate_resource()
                next_process = connector.right_process
                next_processes[next_process.instance_name] = next_process

        # save inputs of the next processes
        for next_process in next_processes.values():
            next_process.save()

    def process_is_ready(self, process: ProcessModel) -> bool:
        if not process.is_runnable:
            return False

        # if it ready, check that all the previous precesses are finished in success
        # it prevent from running a process if an optional input is not set
        for process in self.get_direct_previous_processes(process.instance_name):
            if not process.is_success:
                return False

        return True

    def _run_after_task(self):
        if self.is_finished:
            return

        self._propagate_outerfaces()

        super()._run_after_task()

    def save_after_task(self) -> None:
        """Method called after the task to save the process
        """
        # override the method to update the graph before saving
        self.save_graph()

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

        self._add_process_model(
            process_model=process_model, instance_name=instance_name)

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
            instance_name = self.generate_unique_instance_name(
                process_model.get_process_type().__name__)

        if instance_name in self._processes:
            raise BadRequestException(
                f"Process name '{instance_name}' already exists")
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
                self._processes[key].config.set_values(
                    process_model.config.get_values())
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
        self.remove_interfaces_by_process_name(name)
        self.remove_outerfaces_by_process_name(name)

        if self.layout:
            self.layout.remove_process(name)
        del self._processes[name]

    def get_direct_previous_processes(self, process_name: str) -> Set[ProcessModel]:
        """
        Returns the previous processes of a process.

        :param process: The process
        :type process: Process
        :return: The previous processes
        :rtype: List[Process]
        """
        self._check_instance_name(process_name)
        return {connector.left_process for connector in self.connectors if connector.right_process.instance_name == process_name}

    def get_direct_next_processes(self, process_name: str) -> Set[ProcessModel]:
        """
        Returns the next processes of a process.

        :param process: The process
        :type process: Process
        :return: The next processes
        :rtype: List[Process]
        """
        self._check_instance_name(process_name)
        return {connector.right_process for connector in self.connectors if connector.left_process.instance_name == process_name}

    def get_all_next_processes(
            self, process_name: str, check_parent_protocol: bool = True,
            check_circular_connexion: bool = False) -> Set[ProcessModel]:
        """
        Returns all the next processes of a process in this protocol and parent protocols.

        :param process: The process
        :type process: Process
        :param check_parent_protocol: If True, the next processes of the parent protocol are also returned
        :type check_parent_protocol: bool
        :param check_circular_connexion: If True, check if there is a circular connexion and raise an exception
        :type check_circular_connexion: bool
        :return: The next processes
        :rtype: List[Process]
        """
        return self._get_all_next_processes_recur(process_name=process_name, root_process_name=process_name,
                                                  skip_processes=set(), check_parent_protocol=check_parent_protocol,
                                                  check_circular_connexion=check_circular_connexion)

    def _get_all_next_processes_recur(
            self, process_name: str, root_process_name: str,
            skip_processes: Set[str],
            check_parent_protocol: bool = True,
            check_circular_connexion: bool = False) -> Set[ProcessModel]:
        """
        Returns all the next processes of a process in this protocol and parent protocols.

        :param process: The process
        :type process: Process
        :param check_parent_protocol: If True, the next processes of the parent protocol are also returned
        :type check_parent_protocol: bool
        :param skip_processes: The processes to skip that were already checked
        :type skip_processes: Set[Process]
        :param check_circular_connexion: If True, check if there is a circular connexion and raise an exception
        :type check_circular_connexion: bool
        :return: The next processes
        :rtype: List[Process]
        """
        self._check_instance_name(process_name)

        next_processes: Set[ProcessModel] = self.get_direct_next_processes(
            process_name)
        all_next_processes: Set[ProcessModel] = set(next_processes)

        skip_processes.add(process_name)

        # recursively get the next processes of the next processes
        for process in next_processes:

            if process.instance_name == root_process_name:
                if check_circular_connexion:
                    raise BadRequestException(
                        f"Circular connexion detected with process '{process.get_instance_name_context()}'")
                continue

            if process.instance_name in skip_processes:
                continue

            all_next_processes.update(self._get_all_next_processes_recur(
                process.instance_name, root_process_name, skip_processes, False, check_circular_connexion))

        # get the next processes of the parent protocol
        if check_parent_protocol and self.parent_protocol:
            all_next_processes.update(self.parent_protocol.get_all_next_processes(self.instance_name))

        return all_next_processes

    def get_error_tasks(self) -> List[ProcessModel]:

        error_tasks: List[ProcessModel] = []
        for process in self.processes.values():
            if isinstance(process, ProtocolModel):
                error_tasks.extend(process.get_error_tasks())
            elif process.is_error:
                error_tasks.append(process)

        return error_tasks

    def get_execution_time(self) -> float:
        """Return the execution time of the process

        :return: execution time in seconds
        :rtype: float
        """
        execution_time = 0
        for process in self.processes.values():
            if process.progress_bar.elapsed_time is not None:
                execution_time += process.progress_bar.elapsed_time
        return execution_time

    def has_finished_processes(self) -> bool:
        """Return True if the protocol has finished processes (except the source and sink task)

        :return: True if the protocol has finished processes
        :rtype: bool
        """
        for process in self.processes.values():
            if process.is_finished and not process.is_source_task() and not process.is_sink_task():
                return True
        return False

    def all_processes_are_success(self) -> bool:
        """Return True if all the processes are in success (except the source and sink task)

        :return: True if all the processes are in success
        :rtype: bool
        """
        for process in self.processes.values():
            if not process.is_success and not process.is_source_task() and not process.is_sink_task():
                return False
        return True

    def all_processes_are_draft(self) -> bool:
        """Return True if all the processes are in draft (except the source and sink task)

        :return: True if all the processes are in draft
        :rtype: bool
        """
        for process in self.processes.values():
            if not process.is_draft and not process.is_source_task() and not process.is_sink_task():
                return False
        return True

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
                self.init_connectors_from_graph(
                    self.data["graph"]["links"], check_compatiblity=False)
            else:
                self._connectors = []

    def add_connectors(self, connectors: List[ConnectorSpec]) -> None:
        for connector in connectors:
            self.add_connector(connector["from_process"],
                               connector["from_port"],
                               connector["to_process"],
                               connector["to_port"])

    def add_connector(self, from_process_name: str, from_port_name: str,
                      to_process_name: str, to_port_name: str) -> Connector:
        """
        Adds a connector to the pfrotocol.

        :param connector: The connector
        :type connector: Connector
        """
        # Be sure to have loaded the protocol before adding a connector
        self._load_from_graph()

        # check the ports of the connector
        self._check_port(from_process_name, from_port_name, 'OUT')
        self._check_port(to_process_name, to_port_name, 'IN')

        self._load_connectors()

        connector = self._add_connector(from_process_name, from_port_name,
                                        to_process_name, to_port_name)

        # check if there is a circular connexion
        self.get_all_next_processes(from_process_name, check_circular_connexion=True)

        return connector

    def _add_connector(self, from_process_name: str, from_port_name: str,
                       to_process_name: str, to_port_name: str, check_compatiblity: bool = True) -> Connector:
        """
        Adds a connector to the pfrotocol.

        :param connector: The connector
        :type connector: Connector
        """
        left_proc: ProcessModel = self._processes[from_process_name]
        right_proc: ProcessModel = self._processes[to_process_name]
        connector: Connector = Connector(
            left_process=left_proc,
            right_process=right_proc,
            left_port_name=from_port_name,
            right_port_name=to_port_name, check_compatiblity=check_compatiblity)

        if connector in self._connectors:
            raise BadRequestException("Duplicated connector")
        # use _connector because this is used in the init
        self._connectors.append(connector)

        return connector

    def _check_port(self, process_name: str, port_name: str, port_type: Literal['IN', 'OUT']) -> None:
        process: ProcessModel = self.get_process(process_name)

        if port_type == 'IN':
            # this checks the port
            process.in_port(port_name)
        else:
            # this checks the port
            process.out_port(port_name)

    def init_connectors_from_graph(self, links: ConnectorDict, check_compatiblity: bool = True) -> None:
        self._connectors = []
        # create links
        for link in links:
            left_proc_name: str = link["from"]["node"]
            left_port_name: str = link["from"]["port"]
            right_proc_name = link["to"]["node"]
            right_port_name: str = link["to"]["port"]

            self._add_connector(left_proc_name, left_port_name,
                                right_proc_name, right_port_name,
                                check_compatiblity=check_compatiblity)

    def _get_connectors_linked_to_process(self, process_model: ProcessModel) -> List[Connector]:
        """return the list of connectors connected to a process (input or output)
        """
        connectors: List[Connector] = []

        for connector in self.connectors:
            if connector.is_connected_to(process_model):
                connectors.append(connector)

        return connectors

    def delete_connector_from_right(self, right_process_name: str, right_process_port_name: str) -> Optional[Connector]:
        """ remove the connector which right side is connected to the specified port of the specified process
        return the list of deleted connectors
        """
        connector_to_delete: Optional[Connector] = self.get_connector_from_right(right_process_name,
                                                                                 right_process_port_name)

        if connector_to_delete:
            self._delete_connector_from_list([connector_to_delete])

        return connector_to_delete

    def delete_connectors_from_left(self, left_process_name: str, left_process_port_name: str) -> None:
        """ remove the connector which left side is connected to the specified port of the specified process
        It can remove multiple connectors if there are multiple connectors connected to the same port
        Return the list of deleted connectors
        """
        connectors_to_delete: List[Connector] = self.get_connectors_from_left(
            left_process_name, left_process_port_name)

        self._delete_connector_from_list(connectors_to_delete)

    def _delete_connectors_by_process(self, process_model: ProcessModel) -> List[Connector]:
        """remove all the connectors connected to a process (input or output), return the list of deleted connectors
        """
        connectors_to_delete: List[Connector] = [
            item for item in self.connectors if item.is_connected_to(process_model)]
        self._delete_connector_from_list(connectors_to_delete)
        return connectors_to_delete

    def _delete_connector_from_list(self, connectors_to_delete: List[Connector]) -> None:
        """remove all the connectors in the list
        """
        for connector in connectors_to_delete:
            connector.reset_right_port()
        self._connectors = [
            item for item in self.connectors if item not in connectors_to_delete]

    def get_connector_from_right(self, right_process_name: str, right_process_port_name: str) -> Optional[Connector]:
        """
        Returns a connector by the destination process and port
        """

        for connector in self.connectors:
            if connector.is_right_connected_to(right_process_name, right_process_port_name):
                return connector

        return None

    def get_connectors_from_left(self, left_process_name: str, left_process_port_name: str) -> List[Connector]:
        """
        Returns a connector by the destination process and port
        """
        return [
            item for item in self.connectors
            if item.is_left_connected_to(left_process_name, left_process_port_name)]

    def propagate_resources(self) -> None:
        for connector in self.connectors:
            connector.propagate_resource()

        # save processes to update inputs and outputs
        for process in self.processes.values():
            process.save()

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

    def add_interfaces(self, interfaces: Dict[str, InterfaceSpec]) -> None:
        for key, spec in interfaces.items():
            self.add_interface(
                key, spec["process_instance_name"], spec["port_name"])

    def add_interface(self, name: str, target_process_name: str, target_port_name: str) -> None:
        # to support lazy loading
        self._load_from_graph()
        self._check_port(target_process_name, target_port_name, "IN")
        self._add_interface(name, target_process_name, target_port_name)

    def _add_interface(self, name: str, target_process_name: str, target_port_name: str) -> None:
        target_process = self._processes[target_process_name]
        target_port = target_process.in_port(target_port_name)

        # Create the input's port
        source_port: InPort = self.inputs.create_port(
            name, target_port.resource_spec)
        if target_port.resource_model:
            source_port.resource_model = target_port.resource_model

        # create the interface
        # use _interfaces because this is call during the init
        self._interfaces[name] = Interface(
            name=name, source_process=self, target_process=target_process,
            source_port_name=name, target_port_name=target_port_name)

    def _propagate_interfaces(self):
        """
        Propagate resources through interfaces
        """

        for key, interface in self.interfaces.items():
            port = interface.target_port
            port.resource_model = self.inputs.get_resource_model(key)

    def is_interfaced_with(self, process_instance_name: str) -> bool:
        """
        Returns True if the input poort the process is an interface of the protocol
        """

        interfaces = self.get_interfaces_linked_to_process(
            process_instance_name)
        return len(interfaces) > 0

    def get_interfaces_linked_to_process(self, process_instance_name: str) -> List[Interface]:
        """
        Returns the interfaces linked to a process
        """
        interfaces: List[Interface] = []

        for interface in self.interfaces.values():
            if interface.target_process.instance_name == process_instance_name:
                interfaces.append(interface)

        return interfaces

    def _init_interfaces_from_graph(self, interfaces_dict: Dict) -> None:
        # clear current interfaces
        self._interfaces = {}
        self._inputs = Inputs()

        for key in interfaces_dict:
            # destination port of the interface
            _to: dict = interfaces_dict[key]["to"]
            proc_name: str = _to["node"]
            port_name: str = _to["port"]
            self._add_interface(key, proc_name, port_name)

    def _reset_iofaces(self):
        for interface in self.interfaces.values():
            interface.reset()
        for outerface in self.outerfaces.values():
            outerface.reset()

    def remove_interfaces_by_process_name(self, process_name: str) -> None:
        """
        Remove the interface linked the process with the given name
        """
        to_delete: List[Interface] = self.get_interfaces_linked_to_process(
            process_name)

        for interface in to_delete:
            self.remove_interface(interface.name)

    def remove_interface(self, name: str) -> None:
        """Remove an interface

        :param name: _description_
        :type name: str
        :raises BadRequestException: _description_
        """

        if not name in self.interfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' does not have an interface named '{name}'")

        interface: Interface = self.interfaces[name]
        del self._interfaces[name]

        # delete the corresponding input's port
        self.inputs.remove_port(name)

        # check if the interface is connected in the parent protocol
        if self.parent_protocol:
            # in parent check if a connector is linked to this interface
            connector = self.parent_protocol.get_connector_from_right(
                interface.source_process.instance_name, interface.source_port.name)

            if connector:
                raise BadRequestException(
                    f"The interface '{name}' is connected in the parent protocol '{self.parent_protocol.get_instance_name_context()}', please remove the link connected to this interface in the parent protocol")

            # in parent check if an interface is linked to this interface
            interfaces: List[Interface] = self.parent_protocol.get_interfaces_linked_to_process(
                self.instance_name)

            if len(interfaces) > 0:
                raise BadRequestException(
                    f"The interface '{name}' is connected in the parent protocol '{self.parent_protocol.get_instance_name_context()}', please remove the link connected to this interface in the parent protocol")

        if self.layout:
            self.layout.remove_interface(name)

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

    def add_outerfaces(self, outerfaces: Dict[str, InterfaceSpec]) -> None:
        for key, spec in outerfaces.items():
            self.add_outerface(
                key, spec["process_instance_name"], spec["port_name"])

    def add_outerface(self, name: str, source_process_name: str, source_port_name: str) -> None:
        # to support lazy loading
        self._load_from_graph()
        self._check_port(source_process_name, source_port_name, "OUT")
        self._add_outerface(name, source_process_name, source_port_name)

    def _add_outerface(self, name: str, source_process_name: str, source_port_name: str) -> None:
        source_process = self._processes[source_process_name]
        source_port = source_process.out_port(source_port_name)

        # Create the output's port
        target_port: OutPort = self.outputs.create_port(
            name, source_port.resource_spec)
        if source_port.resource_model:
            target_port.resource_model = source_port.resource_model

        # create the interface
        # use _outerfaces because this is call during the init
        self._outerfaces[name] = Outerface(
            name=name, source_process=source_process, source_port_name=source_port_name,
            target_process=self, target_port_name=name)

    def is_outerfaced_with(self, process_instance_name: str) -> bool:
        """
        Returns True if the input poort the process is an outerface of the protocol
        """

        outerfaces = self.get_outerface_linked_to_process(
            process_instance_name)
        return len(outerfaces) > 0

    def get_outerface_linked_to_process(self, process_instance_name: str) -> List[Outerface]:
        """
        Returns the outerface linked to the process with the given name
        """
        outerfaces: List[Outerface] = []
        for outerface in self.outerfaces.values():
            if outerface.source_process.instance_name == process_instance_name:
                outerfaces.append(outerface)
        return outerfaces

    def _init_outerfaces_from_graph(self, outerfaces_dict: Dict) -> None:
        # clear current interfaces
        self._outerfaces = {}
        self._outputs = Outputs()

        for key in outerfaces_dict:
            # source port of the outerface
            _from: dict = outerfaces_dict[key]["from"]
            proc_name: str = _from["node"]
            port_name: str = _from["port"]
            self._add_outerface(key, proc_name, port_name)

    def remove_outerfaces_by_process_name(self, process_instance_name: str) -> None:
        """
        Remove the outerfaces linked to the process with the given name
        """
        to_delete: List[Outerface] = self.get_outerface_linked_to_process(
            process_instance_name)
        for outerface in to_delete:
            self.remove_outerface(outerface.name)

    def remove_outerface(self, name: str) -> None:
        if not name in self.outerfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' does not have an outerface named '{name}'")

        outerface: Outerface = self._outerfaces[name]
        del self._outerfaces[name]

        # delete the corresponding output
        self.outputs.remove_port(name)

        # check if the outerface is connected in the parent protocol
        if self.parent_protocol:
            # in parent check if a connector is linked to this interface
            connectors = self.parent_protocol.get_connectors_from_left(
                outerface.target_process.instance_name, outerface.target_port.name)

            if len(connectors) > 0:
                raise BadRequestException(
                    f"The outerface '{name}' is connected in the parent protocol '{self.parent_protocol.get_instance_name_context()}', please remove the link connected to this outerface in the parent protocol")

            # in parent check if an outerface is linked to this outerface
            outerfaces: List[Outerface] = self.parent_protocol.get_outerface_linked_to_process(
                self.instance_name)

            if len(outerfaces) > 0:
                raise BadRequestException(
                    f"The outerface '{name}' is connected in the parent protocol '{self.parent_protocol.get_instance_name_context()}', please remove the link connected to this outerface in the parent protocol")

        if self.layout:
            self.layout.remove_outerface(name)

    ############################### JSON #################################

    def dumps_graph(self, process_mode: Literal['full', 'minimize', 'config']) -> dict:
        """ Dumps the JSON graph representing the protocol.

        :param process_mode: mode for the json process:
            - full: full json process (not recursive for the sub-protocol)
            - minimize: minimized json process (only id and typing name)
            - config: json process for config including the layout
        :type process_mode: Literal[full, minimize, config]
        :return: _description_
        :rtype: dict
        """

        graph = {
            "nodes": {},
            "links": [],
            "interfaces": {},
            "outerfaces": {}
        }

        for conn in self.connectors:
            graph['links'].append(conn.to_json())
        for key, process in self.processes.items():
            process_json: dict
            if process_mode == 'minimize':
                process_json = process.get_minimum_json()
            elif process_mode == 'full':
                process_json = process.to_json(deep=False)
            else:
                process_json = process.export_config()

            graph["nodes"][key] = process_json
        for key, interface in self.interfaces.items():
            graph['interfaces'][key] = interface.to_json()
        for key, outerface in self.outerfaces.items():
            graph['outerfaces'][key] = outerface.to_json()

        if process_mode == 'config':
            graph["layout"] = self.layout.to_json() if self.layout else {}

        return graph

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json: dict = super().data_to_json(deep=deep)

        if deep:
            _json["graph"] = self.dumps_graph(process_mode='full')
            _json["graph"]["layout"] = self.layout.to_json() if self.layout else {}

        return _json

    def export_config(self) -> Dict:

        _json = super().export_config()
        _json["graph"] = self.dumps_graph('config')
        return _json

    ############################### OTHER #################################

    def is_protocol(self) -> bool:
        return True

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

    def mark_as_started(self):
        if self.is_running:
            return

        self.ended_at = None
        # specific case for protocol
        # if we start a protocol that was already started
        # we don't want to reset the progress bar
        if not self.progress_bar.is_started:
            self.progress_bar.start()
            self.started_at = DateHelper.now_utc()
            self.progress_bar.add_message(
                f"Start of protocol '{self.get_instance_name_context()}'")
        else:
            self.progress_bar.trigger_second_start()
            self.progress_bar.add_message(
                f"Restart of protocol '{self.get_instance_name_context()}'")
        self.status = ProcessStatus.RUNNING
        self.save()

    def mark_as_partially_run(self):

        # check if there is any process that is finished
        if self.all_processes_are_draft():
            self.mark_as_draft()
        elif self.all_processes_are_success():
            self.mark_as_success()
        else:
            self._mark_as_partially_run()

        if self.parent_protocol and (self.parent_protocol.is_finished or self.parent_protocol.is_partially_run):
            self.parent_protocol.mark_as_partially_run()

        # when we reached the root protocol, mark the experiment as partially run
        if not self.parent_protocol and self.experiment:
            if self.is_partially_run and not self.experiment.is_partially_run:
                self.experiment.mark_as_partially_run()
            elif self.is_draft and not self.experiment.is_draft:
                self.experiment.mark_as_draft()
            elif self.is_success and not self.experiment.is_success:
                self.experiment.mark_as_success()

    def _mark_as_partially_run(self):
        if self.is_partially_run:
            return
        self.progress_bar.add_message(
            "The protocol was modified, marking it as PARTIALLY RUN")
        self.status = ProcessStatus.PARTIALLY_RUN
        self.save()

    def mark_as_draft(self):
        if self.is_draft:
            return
        self.ended_at = None
        self.status = ProcessStatus.DRAFT
        self.error_info = None
        self.save()
