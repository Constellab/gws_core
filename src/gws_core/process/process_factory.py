# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from gws_core.resource.view.viewer import Viewer
from gws_core.task.plug import Sink, Source

from ..config.config import Config
from ..config.config_types import ConfigParams, ConfigParamsDict
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.connector import Connector
from ..io.port import InPort, OutPort
from ..model.typing_manager import TypingManager
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import Protocol, ProtocolCreateConfig
from ..protocol.protocol_exception import ProtocolBuildException
from ..protocol.protocol_model import ProtocolModel
from ..task.task import Task
from ..task.task_model import TaskModel
from .process import Process
from .process_model import ProcessModel, ProcessStatus
from .protocol_sub_process_builder import SubProcessBuilderCreate


class ProcessFactory():
    """Contains methods to instantiate TaskModel and ProtocolModel but it does not save the instances to the database,
    it only create th objects
    """

    ############################################### TASK #################################################

    @classmethod
    def create_task_model_from_type(
            cls, task_type: Type[Task],
            config_params: ConfigParamsDict = None,
            instance_name: str = None) -> TaskModel:
        if not issubclass(task_type, Task):
            name = task_type.__name__ if task_type.__name__ is not None else str(
                task_type)
            raise BadRequestException(
                f"The type {name} is not a Task. It must extend the Task class")

        if not TypingManager.type_is_register(task_type):
            raise BadRequestException(
                f"The task {task_type.full_classname()} is not register. Did you add the @task_decorator decorator on your task class ?")

        task_model: TaskModel = TaskModel()
        task_model.set_process_type(task_type._typing_name)

        # Specific case for the source, to set the source_config id is provided
        if task_type == Source and config_params.get(Source.config_name):
            task_model.source_config_id = config_params.get(
                Source.config_name)

        config: Config = Config()
        config.set_specs(task_type.config_specs)
        if config_params:
            config.set_values(config_params)

        cls._init_process_model(process_model=task_model, config=config, instance_name=instance_name)

        return task_model

    @classmethod
    def create_task_model_from_typing_name(
            cls, typing_name: str, config_params: ConfigParamsDict = None, instance_name: str = None) -> TaskModel:
        task_type: Type[Task] = TypingManager.get_type_from_name(typing_name=typing_name)
        return cls.create_task_model_from_type(
            task_type=task_type, config_params=config_params, instance_name=instance_name)

    ############################################### PROTOCOL #################################################

    @classmethod
    def create_protocol_model_from_type(cls, protocol_type: Type[Protocol],
                                        config_params: ConfigParamsDict = None,
                                        instance_name: str = None) -> ProtocolModel:

        try:
            if not issubclass(protocol_type, Protocol):
                name = protocol_type.__name__ if protocol_type.__name__ is not None else str(
                    protocol_type)
                raise BadRequestException(
                    f"The type {name} is not a Protocol. It must extend the Protcol class")

            if not TypingManager.type_is_register(protocol_type):
                raise BadRequestException(
                    f"The protocol {protocol_type.full_classname()} is not register. Did you add the @ProtocolDecorator decorator on your protocol class ?")

            protocol_model: ProtocolModel = ProtocolModel()
            protocol_model.set_process_type(protocol_type._typing_name)

            config: Config = Config()
            cls._init_process_model(process_model=protocol_model, config=config, instance_name=instance_name)

            protocol: Protocol = protocol_type.instantiate_protocol()
            create_config: ProtocolCreateConfig = protocol.get_create_config()

            # Create the process and protocol (recursive)
            processes: Dict[str, ProcessModel] = {}
            for key, proc in create_config["process_specs"].items():
                try:
                    processes[key] = ProcessFactory.create_process_model_from_type(
                        proc.process_type, proc.get_config_params(), proc.instance_name)
                except ProtocolBuildException as err:
                    raise err
                except Exception as err:
                    raise ProtocolBuildException.from_exception('Task', key, err)

            # Set the protocol interfaces
            interfaces: Dict[str, InPort] = {}
            for key, interface in create_config["interfaces"].items():
                interfaces[key] = processes[interface["process_instance_name"]].in_port(interface["port_name"])

            # Set the protocol outerfaces
            outerfaces: Dict[str, OutPort] = {}
            for key, outerface in create_config["outerfaces"].items():
                outerfaces[key] = processes[outerface["process_instance_name"]].out_port(outerface["port_name"])

            # Set the connectors
            connectors: List[Connector] = []
            for connector in create_config["connectors"]:
                from_proc: ProcessModel = processes[connector["from_process"]]
                to_proc: ProcessModel = processes[connector["to_process"]]
                connectors.append(Connector(
                    out_port=from_proc.out_port(connector["from_port"]),
                    in_port=to_proc.in_port(connector["to_port"])))

            # create the protocol from a statis protocol class
            return cls._build_protocol_model(
                protocol_model=protocol_model,
                processes=processes,
                connectors=connectors,
                interfaces=interfaces,
                outerfaces=outerfaces
            )
        except ProtocolBuildException as err:
            raise ProtocolBuildException.from_build_exception(parent_instance_name=instance_name, exception=err)
        except Exception as err:
            raise ProtocolBuildException.from_exception('Protocol', instance_name, err)

    @classmethod
    def create_protocol_empty(cls, instance_name: str = None) -> ProtocolModel:
        return cls.create_protocol_model_from_data(instance_name=instance_name)

    @classmethod
    def create_protocol_model_from_data(cls, processes: Dict[str, ProcessModel] = None,
                                        connectors: List[Connector] = None,
                                        interfaces: Dict[str, InPort] = None,
                                        outerfaces: Dict[str, OutPort] = None,
                                        instance_name: str = None) -> ProtocolModel:
        protocol_model: ProtocolModel = ProtocolModel()

        # Use the Protocol default type because the protocol is not linked to a specific type
        protocol_model.process_typing_name = Protocol._typing_name

        cls._init_process_model(
            process_model=protocol_model, config=Config(), instance_name=instance_name)

        # create the protocol from a statis protocol class
        return cls._build_protocol_model(
            protocol_model=protocol_model,
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
        )

    @classmethod
    def _build_protocol_model(cls, protocol_model: ProtocolModel, processes: Dict[str, ProcessModel] = None,
                              connectors: List[Connector] = None,
                              interfaces: Dict[str, InPort] = None,
                              outerfaces: Dict[str, OutPort] = None) -> ProtocolModel:
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
            if not isinstance(proc, ProcessModel):
                raise BadRequestException(
                    "The dictionnary of processes must contain instances of ProcessModel")
            protocol_model.add_process_model(proc, name)

        # set connectors
        for conn in connectors:
            if not isinstance(conn, Connector):
                raise BadRequestException(
                    "The list of connector must contain instances of Connectors")
            protocol_model.add_connector(conn)

        # set interfaces
        protocol_model.add_interfaces(interfaces)
        protocol_model.add_outerfaces(outerfaces)
        # refresh the json graph
        protocol_model.refresh_graph_from_dump()

        return protocol_model

    @classmethod
    def create_protocol_model_from_graph(cls, graph: dict) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        # create an empty protocol
        protocol: ProtocolModel = cls.create_protocol_model_from_type(
            protocol_type=Protocol)

        cls._create_protocol_model_from_graph_recur(protocol=protocol, graph=graph)
        return protocol

    @classmethod
    def _create_protocol_model_from_graph_recur(cls, protocol: ProtocolModel, graph: dict) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        protocol.build_from_graph(
            graph=graph, sub_process_factory=SubProcessBuilderCreate())

        for key, process in protocol.processes.items():
            if isinstance(process, ProtocolModel):
                cls._create_protocol_model_from_graph_recur(
                    protocol=process, graph=graph["nodes"][key]["data"]["graph"])

        # Init the connector afterward because its needs the child to init correctly
        protocol.init_connectors_from_graph(graph["links"])

        return protocol

    ############################################### PROCESS  #################################################

    @classmethod
    def create_process_model_from_type(
            cls, process_type: Type[Process],
            config_params: ConfigParamsDict = None,
            instance_name: str = None) -> TaskModel:
        if issubclass(process_type, Task):
            return cls.create_task_model_from_type(process_type, config_params, instance_name)
        elif issubclass(process_type, Protocol):
            return cls.create_protocol_model_from_type(process_type, config_params, instance_name)
        else:
            name = process_type.__name__ if process_type.__name__ is not None else str(
                process_type)
            raise BadRequestException(
                f"The type {name} is not a Process nor a Protocol. It must extend the on of the classes")

    @classmethod
    def create_process_model_from_typing_name(
            cls, typing_name: str, config_params: ConfigParamsDict = None, instance_name: str = None) -> TaskModel:
        process_type: Type[Process] = TypingManager.get_type_from_name(typing_name=typing_name)
        return cls.create_process_model_from_type(
            process_type=process_type, config_params=config_params, instance_name=instance_name)

    @classmethod
    def _init_process_model(
            cls, process_model: ProcessModel, config: Config, instance_name: str = None) -> None:

        process_model.status = ProcessStatus.DRAFT
        # Set the config
        process_model.config = config

        # Set the progress_bar
        progress_bar: ProgressBar = ProgressBar(
            process_id=process_model.id, process_typing_name=process_model.process_typing_name)
        process_model.progress_bar = progress_bar

        if instance_name is not None:
            process_model.instance_name = instance_name
        else:
            # Init the instance_name if it does not exists
            process_model.instance_name = process_model.id

    ############################################### PROCESS  #################################################

    @classmethod
    def copy_process(cls, process_model: ProcessModel) -> ProtocolModel:
        if isinstance(process_model, TaskModel):
            return cls.copy_task(process_model)
        else:
            return cls.copy_protocol(process_model)

    @classmethod
    def copy_task(cls, task_model: TaskModel) -> TaskModel:
        return cls.create_task_model_from_type(
            task_model.get_process_type(),
            task_model.config.get_values(),
            task_model.instance_name)

    @classmethod
    def copy_protocol(cls, protocol_model: ProtocolModel) -> ProtocolModel:
        """Copy a protocol, copy sub nodes,copy interface, outerface and connecter

        :param protocol_model: [description]
        :type protocol_model: ProtocolModel
        :return: [description]
        :rtype: ProtocolModel
        """
        new_protocol_model: ProtocolModel = cls.create_protocol_empty()
        new_protocol_model.set_process_type(protocol_model.get_process_type()._typing_name)

        # If the instance name is the same as the id, don't set it
        instance_name = protocol_model.instance_name if protocol_model.instance_name != protocol_model.id else None
        cls._init_process_model(
            process_model=protocol_model, config=protocol_model.config.copy(),
            instance_name=instance_name)

        # copy all the sub process
        for key, process in protocol_model.processes.items():
            new_protocol_model.add_process_model(cls.copy_process(process), key)

        # copy the data and then refresh it to update information
        new_protocol_model._init_interfaces_from_graph(protocol_model.data["graph"]["interfaces"])
        new_protocol_model._init_outerfaces_from_graph(protocol_model.data["graph"]["outerfaces"])
        new_protocol_model.init_connectors_from_graph(protocol_model.data["graph"]["links"])
        new_protocol_model.refresh_graph_from_dump()

        return new_protocol_model

      ############################################### SPECIFIC #################################################

    @classmethod
    def create_source(cls, resouce_id: str) -> TaskModel:
        return cls.create_task_model_from_type(Source, {Source.config_name: resouce_id})

    @classmethod
    def create_sink(cls) -> TaskModel:
        return cls.create_task_model_from_type(Sink)

    @classmethod
    def create_viewer(cls, resource_typing_name: str) -> TaskModel:
        return cls.create_task_model_from_type(Viewer, {Viewer.resource_config_name: resource_typing_name})
