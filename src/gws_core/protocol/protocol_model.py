

import re
from typing import Dict, List, Literal, Optional, Set

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.protocol.protocol_dto import (ConnectorDTO, IOFaceDTO,
                                            ProcessConfigDTO, ProtocolDTO,
                                            ProtocolFullDTO,
                                            ProtocolGraphConfigDTO,
                                            ProtocolMinimumDTO)
from gws_core.protocol.protocol_exception import \
    IOFaceConnectedToTheParentDeleteException
from gws_core.protocol.protocol_spec import ConnectorSpec, InterfaceSpec
from gws_core.task.plug.input_task import InputTask

from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.model.db_field import SerializableDBField
from ..io.connector import Connector
from ..io.ioface import IOface
from ..io.port import InPort, OutPort
from ..process.process_model import ProcessModel
from ..process.process_types import ProcessStatus
from ..process.protocol_sub_process_builder import (
    ProtocolSubProcessBuilder, SubProcessBuilderReadFromDb)
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
    _interfaces: Dict[str, IOface] = {}
    _outerfaces: Dict[str, IOface] = {}
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
        self.is_archived = archive
        return self.save()

    @transaction()
    def reset(self) -> 'ProtocolModel':
        """
        Reset the protocol
        """

        super().reset()
        for process in self.processes.values():
            process.reset()

        try:
            # auto execute the source task
            self.run_auto_run_processes()

            # re-propagate the resources (because source task has been executed)
            # and save processes
            self.propagate_resources()
        # Catch to be sure the reset works, it should not block the reset
        except Exception as e:
            Logger.error(
                f"Error while resetting the protocol on auto run or propagate resource. Continue reset. Error : {e}")

        return self.save_graph()

    def save_graph(self) -> 'ProtocolModel':
        self.refresh_graph_from_dump()
        return self.save()

    def set_scenario(self, scenario):
        super().set_scenario(scenario)
        for process in self.processes.values():
            process.set_scenario(scenario)

    @transaction()
    def delete_instance(self, *args, **kwargs):
        """Override delete instance to delete all the sub processes

        :return: [description]
        :rtype: [type]
        """
        for process in self.processes.values():
            process.delete_instance()

        return super().delete_instance(*args, **kwargs)

    ############################### GRAPH #################################

    def _load_from_graph(self) -> None:

        if self._is_loaded:
            return

        graph = self.get_graph()
        if graph is None:
            self._is_loaded = True
            return

        sub_process_factory = SubProcessBuilderReadFromDb(graph)

        # init processes and sub processes
        self.init_processes_from_graph(sub_process_factory)

        # init interfaces and outerfaces
        self._interfaces = IOface.load_from_dto_dict(graph.interfaces)
        self._outerfaces = IOface.load_from_dto_dict(graph.outerfaces)
        self._is_loaded = True

    def refresh_graph_from_dump(self) -> None:
        """Refresh the graph json object inside the data from the dump method
        """
        self.data["graph"] = self.to_protocol_minimum_dto().to_json_dict()

    def get_graph(self) -> ProtocolMinimumDTO:
        """Return the graph json object
        """
        graph = self.data["graph"]
        if not isinstance(graph, dict):
            return None
        if not isinstance(graph.get("nodes"), dict) or not graph["nodes"]:
            return None
        return ProtocolMinimumDTO.from_json(graph)

    ############################### RUN #################################

    def _run_before_task(self):
        if self.is_running or self.is_finished:
            return
        self._propagate_interfaces()
        if not self.scenario:
            raise BadRequestException("No scenario defined")
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
                "The process cannot be run because it is not ready. Are the previous processes run and are the inputs provided ?")

        self._run_before_task()
        self.mark_as_started()
        self._run_process(process)

        # auto run the next process if it is auto run
        self.run_auto_run_processes()

        self._run_after_task()

    def run_auto_run_processes(self) -> None:
        """Run all the auto run processes of the protocol
        """
        for process in self.processes.values():
            if process.is_auto_run() and process.is_runnable and process.config.mandatory_values_are_set():
                self._run_process(process)

    def _run_protocol(self) -> None:
        """
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
        self.refresh_status(refresh_parent=False)

        # save the protocol graph
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
        if not self.is_root_process() and not process_model.is_enable_in_sub_protocol():
            raise BadRequestException(
                f"The process '{process_model.name}' cannot be added to a sub protocol")

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

        # check instance name, it can contain only letters, numbers and underscores using regex
        if re.match(r'^\w+$', instance_name) is None:
            raise BadRequestException(
                f"Invalid instance name '{instance_name}', it can contain only letters, numbers and underscores")

        if instance_name in self._processes:
            raise BadRequestException(
                f"Process name '{instance_name}' already exists")
        if process_model in self._processes.items():
            raise BadRequestException(f"Process '{instance_name}' duplicate")

        process_model.set_parent_protocol(self)

        # set instance name in process and add process
        process_model.instance_name = instance_name
        self._processes[instance_name] = process_model

    def init_processes_from_graph(self, sub_process_factory: ProtocolSubProcessBuilder) -> None:
        # create nodes
        process_models: Dict[str, ProcessModel] = sub_process_factory.instantiate_processes()
        for key, process_model in process_models.items():

            # If the process already exists
            if key in self._processes:
                raise Exception(f"Process with instance name '{key}' already exists")
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

    def get_process_by_instance_path(self, instance_path: str) -> ProcessModel:
        """
        Returns a process by its instance path.

        :return: The process
        :rtype": Process
        """

        instance_names = instance_path.split('.')

        process = self.get_process(instance_names[0])

        if len(instance_names) == 1:
            return process

        # if we need to get a sub process
        if not isinstance(process, ProtocolModel):
            raise BadRequestException(f"Process '{process.get_instance_name_context()}' is not a protocol")

        return process.get_process_by_instance_path('.'.join(instance_names[1:]))

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

    def get_all_processes_flatten_sort_by_start_date(self) -> List[ProcessModel]:
        """Return all the processes of the protocol and its sub protocols, sorted by start date

        :return: all the processes of the protocol and its sub protocols
        :rtype: List[ProcessModel]
        """
        all_processes: List[ProcessModel] = []
        for process in self.processes.values():
            all_processes.append(process)

            if isinstance(process, ProtocolModel):
                all_processes.extend(process.get_all_processes_flatten_sort_by_start_date())

        # sort all processes by end_date, with null end_date at the end
        all_processes.sort(key=lambda x: x.progress_bar.started_at
                           if x.progress_bar.started_at else DateHelper.MAX_DATE)

        return all_processes

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
        """Return True if the protocol has finished processes (except the auto run processes)

        :return: True if the protocol has finished processes
        :rtype: bool
        """
        for process in self.processes.values():
            if process.is_finished and not process.is_auto_run():
                return True
        return False

    def all_processes_are_success(self) -> bool:
        """Return True if all the processes are in success

        :return: True if all the processes are in success
        :rtype: bool
        """
        for process in self.processes.values():
            if not process.is_success:
                return False
        return True

    def all_processes_are_draft(self) -> bool:
        """Return True if all the processes are in draft

        :return: True if all the processes are in draft
        :rtype: bool
        """
        for process in self.processes.values():
            if not process.is_draft and not process.is_auto_run():
                return False
        return True

    def get_running_task(self) -> Optional[ProcessModel]:
        """Return the running process, go through all the sub protocols

        :return: the running process
        :rtype: ProcessModel
        """
        for process in self.processes.values():
            if process.is_running:
                if isinstance(process, ProtocolModel):
                    return process.get_running_task()
                return process
        return None

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
                links_dto = ConnectorDTO.from_json_list(self.data["graph"]["links"])
                self.init_connectors_from_graph(links_dto, check_compatiblity=False)
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

        # propagate the resource if the left port has a resource
        connector.propagate_resource()

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

    def init_connectors_from_graph(self, links: List[ConnectorDTO], check_compatiblity: bool = True) -> None:
        self._connectors = []
        # create links
        for link in links:
            self._add_connector(link.from_.node, link.from_.port,
                                link.to.node, link.to.port,
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
        affected_processes: Set[ProcessModel] = set()
        for connector in self.connectors:
            if connector.propagate_resource():
                affected_processes.add(connector.right_process)

        # save processes to update inputs and outputs
        for process in affected_processes:
            process.save()

    ############################### INTERFACE #################################

    @property
    def interfaces(self) -> Dict[str, IOface]:
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

    def add_interfaces_from_dto(self, interfaces: Dict[str, IOFaceDTO]) -> None:
        for key, spec in interfaces.items():
            self.add_interface(
                key, spec.process_instance_name, spec.port_name)

    def add_interface(self, name: str, process_name: str, port_name: str) -> IOface:
        # to support lazy loading
        self._load_from_graph()
        self._check_port(process_name, port_name, "IN")

        if name in self.interfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' already has an interface named '{name}'")

        return self._add_interface(name, process_name, port_name)

    def _add_interface(self, name: str, process_name: str, port_name: str) -> IOface:
        target_process = self._processes[process_name]
        target_port = target_process.in_port(port_name)

        # Create the input's port
        source_port: InPort = self.inputs.create_port(
            name, target_port.resource_spec)
        if target_port.get_resource_model():
            source_port.set_resource_model(target_port.get_resource_model())

        # create the interface
        # use _interfaces because this is call during the init
        self._interfaces[name] = IOface(
            name=name,
            process_instance_name=process_name,
            port_name=port_name
        )
        return self._interfaces[name]

    def _propagate_interfaces(self):
        """
        Propagate resources through interfaces
        """

        for key, interface in self.interfaces.items():
            process = self.get_process(interface.process_instance_name)
            port = process.in_port(interface.port_name)
            port.set_resource_model(self.inputs.get_resource_model(key))

    def is_interfaced_with(self, process_instance_name: str) -> bool:
        """
        Returns True if the input poort the process is an interface of the protocol
        """

        interfaces = self.get_interfaces_linked_to_process(
            process_instance_name)
        return len(interfaces) > 0

    def get_interfaces_linked_to_process(self, process_instance_name: str) -> List[IOface]:
        """
        Returns the interfaces linked to a process
        """
        interfaces: List[IOface] = []

        for interface in self.interfaces.values():
            if interface.process_instance_name == process_instance_name:
                interfaces.append(interface)

        return interfaces

    def remove_interfaces_by_process_name(self, process_name: str) -> None:
        """
        Remove the interface linked the process with the given name
        """
        to_delete: List[IOface] = self.get_interfaces_linked_to_process(
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

        interface: IOface = self.interfaces[name]
        # check if the interface is connected in the parent protocol
        if self.parent_protocol:
            # in parent check if a connector is linked to this interface
            connector = self.parent_protocol.get_connector_from_right(
                self.instance_name, interface.name)

            if connector:
                raise IOFaceConnectedToTheParentDeleteException(
                    'interface', name, self.parent_protocol.get_instance_name_context())

            # in parent check if an interface is linked to this interface
            interfaces: List[IOface] = self.parent_protocol.get_interfaces_linked_to_process(
                self.instance_name)

            if len(interfaces) > 0:
                raise IOFaceConnectedToTheParentDeleteException(
                    'interface', name, self.parent_protocol.get_instance_name_context())

        del self._interfaces[name]

        # delete the corresponding input's port
        self.inputs.remove_port(name)

        if self.layout:
            self.layout.remove_interface(name)

    def port_is_interface(self, process_instance_name: str, port_name) -> bool:
        """ Return True if the port of the process is an interface of the protocol
        """
        for interface in self.interfaces.values():
            if interface.process_instance_name == process_instance_name and interface.port_name == port_name:
                return True

        return False

    def generate_interface_name(self) -> str:
        """Generate a unique interface name
        """
        return self._generate_unique_io_name(self.interfaces, "interface")

    def set_interfaces(self, interfaces: Dict[str, IOface]) -> None:
        self._interfaces = interfaces

    ############################### OUTERFACE #################################

    @property
    def outerfaces(self) -> Dict[str, IOface]:
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
            process = self.get_process(outerface.process_instance_name)
            port = process.out_port(outerface.port_name)
            # port = outerface.source_port
            self.outputs.set_resource_model(key, port.get_resource_model())

    def add_outerfaces(self, outerfaces: Dict[str, InterfaceSpec]) -> None:
        for key, spec in outerfaces.items():
            self.add_outerface(
                key, spec["process_instance_name"], spec["port_name"])

    def add_outerfaces_from_dto(self, outerfaces: Dict[str, IOFaceDTO]) -> None:
        for key, spec in outerfaces.items():
            self.add_outerface(
                key, spec.process_instance_name, spec.port_name)

    def add_outerface(self, name: str, process_name: str, port_name: str) -> IOface:
        # to support lazy loading
        self._load_from_graph()
        self._check_port(process_name, port_name, "OUT")

        if name in self.outerfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' already has an outerface named '{name}'")

        return self._add_outerface(name, process_name, port_name)

    def _add_outerface(self, name: str, process_name: str, port_name: str) -> IOface:
        source_process = self._processes[process_name]
        source_port = source_process.out_port(port_name)

        # Create the output's port
        target_port: OutPort = self.outputs.create_port(
            name, source_port.resource_spec)
        if source_port.get_resource_model():
            target_port.set_resource_model(source_port.get_resource_model())

        # create the interface
        # use _outerfaces because this is call during the init
        self._outerfaces[name] = IOface(
            name=name,
            process_instance_name=process_name,
            port_name=port_name
        )
        return self._outerfaces[name]

    def is_outerfaced_with(self, process_instance_name: str) -> bool:
        """
        Returns True if the input poort the process is an outerface of the protocol
        """

        outerfaces = self.get_outerface_linked_to_process(
            process_instance_name)
        return len(outerfaces) > 0

    def get_outerface_linked_to_process(self, process_instance_name: str) -> List[IOface]:
        """
        Returns the outerface linked to the process with the given name
        """
        outerfaces: List[IOface] = []
        for outerface in self.outerfaces.values():
            if outerface.process_instance_name == process_instance_name:
                outerfaces.append(outerface)
        return outerfaces

    def remove_outerfaces_by_process_name(self, process_instance_name: str) -> None:
        """
        Remove the outerfaces linked to the process with the given name
        """
        to_delete: List[IOface] = self.get_outerface_linked_to_process(
            process_instance_name)
        for outerface in to_delete:
            self.remove_outerface(outerface.name)

    def remove_outerface(self, name: str) -> None:
        if not name in self.outerfaces:
            raise BadRequestException(
                f"The protocol '{self.get_instance_name_context()}' does not have an outerface named '{name}'")

        outerface: IOface = self._outerfaces[name]
        # check if the outerface is connected in the parent protocol
        if self.parent_protocol:
            # in parent check if a connector is linked to this interface
            connectors = self.parent_protocol.get_connectors_from_left(
                self.instance_name, outerface.name)

            if len(connectors) > 0:
                raise IOFaceConnectedToTheParentDeleteException(
                    'outerface', name, self.parent_protocol.get_instance_name_context())

            # in parent check if an outerface is linked to this outerface
            outerfaces: List[IOface] = self.parent_protocol.get_outerface_linked_to_process(
                self.instance_name)

            if len(outerfaces) > 0:
                raise IOFaceConnectedToTheParentDeleteException(
                    'outerface', name, self.parent_protocol.get_instance_name_context())

        del self._outerfaces[name]

        # delete the corresponding output
        self.outputs.remove_port(name)
        if self.layout:
            self.layout.remove_outerface(name)

    def generate_outerface_name(self) -> str:
        """Generate a unique outerface name
        """
        return self._generate_unique_io_name(self.outerfaces, "outerface")

    def set_outerfaces(self, outerfaces: Dict[str, IOface]) -> None:
        self._outerfaces = outerfaces

    ############################### JSON #################################

    def to_config_dto(self, ignore_source_config: bool = False) -> ProcessConfigDTO:
        dto = super().to_config_dto()
        dto.graph = self.to_protocol_config_dto(ignore_source_config=ignore_source_config)
        return dto

    def to_protocol_config_dto(self, ignore_source_config: bool = False) -> ProtocolGraphConfigDTO:
        return ProtocolGraphConfigDTO(
            nodes={key: process.to_config_dto(ignore_source_config) for key, process in self.processes.items()},
            links=[connector.to_dto() for connector in self.connectors],
            interfaces={key: interface.to_dto() for key, interface in self.interfaces.items()},
            outerfaces={key: outerface.to_dto() for key, outerface in self.outerfaces.items()},
            layout=self.layout.to_dto() if self.layout else None
        )

    def to_protocol_minimum_dto(self) -> ProtocolMinimumDTO:
        return ProtocolMinimumDTO(
            nodes={key: process.to_minimum_dto() for key, process in self.processes.items()},
            links=[connector.to_dto() for connector in self.connectors],
            interfaces={key: interface.to_dto() for key, interface in self.interfaces.items()},
            outerfaces={key: outerface.to_dto() for key, outerface in self.outerfaces.items()}
        )

    def to_protocol_full_dto(self) -> ProtocolFullDTO:
        return ProtocolFullDTO(
            nodes={key: process.to_dto() for key, process in self.processes.items()},
            links=[connector.to_dto() for connector in self.connectors],
            interfaces={key: interface.to_dto() for key, interface in self.interfaces.items()},
            outerfaces={key: outerface.to_dto() for key, outerface in self.outerfaces.items()},
            layout=self.layout.to_dto() if self.layout else None
        )

    def to_protocol_dto(self) -> ProtocolDTO:
        process_dto = self.to_dto()

        return ProtocolDTO(
            **process_dto.to_json_dict(),
            data=self.to_protocol_full_dto()
        )

    ############################### OTHER #################################

    def is_protocol(self) -> bool:
        return True

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

    def refresh_status(self, refresh_parent: bool = True):
        """Refresh the status of the protocol based on the status of its processes """

        # check if there is any process that is finished
        if self.all_processes_are_draft():
            self.mark_as_draft()
        elif self.all_processes_are_success():
            self.mark_as_success()
        else:
            self._mark_as_partially_run()

        if refresh_parent:
            if self.parent_protocol and (
                    self.parent_protocol.is_finished or self.parent_protocol.is_partially_run):
                self.parent_protocol.refresh_status()

            # when we reached the root protocol, mark the scenario as partially run
            if not self.parent_protocol and self.scenario:
                if self.is_partially_run and not self.scenario.is_partially_run:
                    self.scenario.mark_as_partially_run()
                elif self.is_draft and not self.scenario.is_draft:
                    self.scenario.mark_as_draft()
                elif self.is_success and not self.scenario.is_success:
                    self.scenario.mark_as_success()

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
        self.set_error_info(None)
        self.save()

    def check_is_updatable(self, error_if_finished: bool = True) -> None:
        super().check_is_updatable(error_if_finished)
        if self.scenario:
            self.scenario.check_is_updatable()

            if self.scenario.is_running_or_waiting:
                raise BadRequestException(
                    detail="The scenario is running or in queue, you can't update it")

    def get_input_resource_model_ids(self) -> Set[str]:
        """
        :return: return all the resource ids configured as input of this protocol
        :rtype: Set[str]
        """
        resource_ids: Set[str] = set()
        for process in self.processes.values():
            if process.is_input_task():
                resource_id = InputTask.get_resource_id_from_config(process.config.get_values())
                if resource_id:
                    resource_ids.add(resource_id)
        return resource_ids

    def replace_io_process_with_ioface(self):
        """Method to replace each Input process with an interface
        and each Output process with an outerface. It does not replace on sub protocols
        """
        new_interfaces: Dict[str, IOFaceDTO] = {}
        new_outerfaces: Dict[str, IOFaceDTO] = {}

        processes_to_remove: List[str] = []

        for process in self.processes.values():
            if process.is_input_task():

                # convert the output connexions of Input process to interfaces
                connectors = self._get_connectors_linked_to_process(process)
                i = 0
                for connector in connectors:
                    interface_name = f"{process.instance_name}_{str(i)}"
                    new_interfaces[interface_name] = IOFaceDTO(
                        name=interface_name, process_instance_name=connector.right_process.instance_name,
                        port_name=connector.right_port.name)

                    i += 1

                processes_to_remove.append(process.instance_name)
            elif process.is_output_task():

                # convert the input connexions of Output process to outerfaces
                connectors = self._get_connectors_linked_to_process(process)
                i = 0
                for connector in connectors:
                    outerface_name = f"{process.instance_name}_{str(i)}"
                    new_outerfaces[outerface_name] = IOFaceDTO(
                        name=outerface_name, process_instance_name=connector.left_process.instance_name,
                        port_name=connector.left_port.name)

                    i += 1
                processes_to_remove.append(process.instance_name)

        # remove the process before adding the interfaces, so the ports are not used
        for process_name in processes_to_remove:
            self.remove_process(process_name)

        self.add_interfaces_from_dto(new_interfaces)
        self.add_outerfaces_from_dto(new_outerfaces)

    def _generate_unique_io_name(self, io_dict: Dict[str, IOface],
                                 name: str) -> str:
        """Generate a unique name for an io dict
        """

        if not name in io_dict:
            return name

        count: int = 1
        while f"{name}_{count}" in io_dict:
            count += 1

        return f"{name}_{count}"
