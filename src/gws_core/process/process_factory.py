# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from ..config.config import Config
from ..config.config_spec import ConfigValues
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.connector import Connector
from ..io.port import Port
from ..model.typing_manager import TypingManager
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import (CONST_PROTOCOL_TYPING_NAME, Protocol,
                                 ProtocolCreateConfig)
from ..protocol.protocol_exception import ProtocolBuildException
from ..protocol.protocol_model import ProtocolModel
from ..task.task import Task
from ..task.task_model import TaskModel
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .process import Process
from .process_model import ProcessModel, ProcessStatus
from .sub_process_factory import SubProcessFactoryCreate


class ProcessFactory():
    """Contains methods to instantiate TaskModel and ProtocolModel but it does not save the instances to the database,
    it only create th objects
    """

    ############################################### TASK #################################################

    @classmethod
    def create_task_model_from_type(
            cls, task_type: Type[Task],
            config_values: ConfigValues = None,
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
        task_model.set_task_type(task_type._typing_name)

        config: Config = Config(specs=task_type.config_specs)
        if config_values:
            config.set_params(config_values)

        cls._init_process_model(process_model=task_model, config=config, instance_name=instance_name)

        return task_model

    @classmethod
    def create_task_model_from_typing_name(
            cls, typing_name: str, config_values: ConfigValues = None, instance_name: str = None) -> TaskModel:
        task_type: Type[Task] = TypingManager.get_type_from_name(typing_name=typing_name)
        return cls.create_task_model_from_type(
            task_type=task_type, config_values=config_values, instance_name=instance_name)

    ############################################### PROTOCOL #################################################

    @classmethod
    def create_protocol_model_from_type(cls, protocol_type: Type[Protocol],
                                        config_values: ConfigValues = None,
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
            protocol_model.set_protocol_type(protocol_type)

            config: Config = Config(specs=protocol_type.config_specs)
            if config_values:
                config.set_params(config_values)

            cls._init_process_model(process_model=protocol_model, config=config, instance_name=instance_name)

            protocol: Protocol = protocol_type()
            protocol.configure_protocol(config.get_and_check_params())
            create_config: ProtocolCreateConfig = protocol.get_create_config()

            # Create the process and protocol (recursive)
            processes: Dict[str, ProcessModel] = {}
            for key, proc in create_config["process_specs"].items():
                try:
                    processes[key] = ProcessFactory.create_process_model_from_type(
                        proc.process_type, proc.get_config_values(), proc.instance_name)
                except ProtocolBuildException as err:
                    raise err
                except Exception as err:
                    raise ProtocolBuildException.from_exception('Process', key, err)

            # Set the protocol interfaces
            interfaces: Dict[str, Port] = {}
            for key, interface in create_config["interfaces"].items():
                interfaces[key] = processes[interface["process_instance_name"]].in_port(interface["port_name"])

            # Set the protocol outerfaces
            outerfaces: Dict[str, Port] = {}
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
    def create_protocol_empty(cls) -> ProtocolModel:
        return cls.create_protocol_model_from_data()

    @classmethod
    def create_protocol_model_from_data(cls, processes: Dict[str, ProcessModel] = None,
                                        connectors: List[Connector] = None,
                                        interfaces: Dict[str, Port] = None,
                                        outerfaces: Dict[str, Port] = None,
                                        instance_name: str = None) -> ProtocolModel:
        protocol_model: ProtocolModel = ProtocolModel()

        # Use the Protocol default type because the protocol is not linked to a specific type
        protocol_model.process_typing_name = CONST_PROTOCOL_TYPING_NAME

        cls._init_process_model(
            process_model=protocol_model, config=Config({}), instance_name=instance_name)

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
                              interfaces: Dict[str, Port] = None,
                              outerfaces: Dict[str, Port] = None) -> ProtocolModel:
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
            protocol_model.add_process_model(name, proc)

        # set connectors
        for conn in connectors:
            if not isinstance(conn, Connector):
                raise BadRequestException(
                    "The list of connector must contain instances of Connectors")
            protocol_model.add_connector(conn)

        # set interfaces
        protocol_model.set_interfaces(interfaces)
        protocol_model.set_outerfaces(outerfaces)
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
            graph=graph, sub_process_factory=SubProcessFactoryCreate())

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
            config_values: ConfigValues = None,
            instance_name: str = None) -> TaskModel:
        if issubclass(process_type, Task):
            return cls.create_task_model_from_type(process_type, config_values, instance_name)
        elif issubclass(process_type, Protocol):
            return cls.create_protocol_model_from_type(process_type, config_values, instance_name)
        else:
            name = process_type.__name__ if process_type.__name__ is not None else str(
                process_type)
            raise BadRequestException(
                f"The type {name} is not a Process nor a Protocol. It must extend the on of the classes")

    @classmethod
    def create_process_model_from_typing_name(
            cls, typing_name: str, config_values: ConfigValues = None, instance_name: str = None) -> TaskModel:
        process_type: Type[Process] = TypingManager.get_type_from_name(typing_name=typing_name)
        return cls.create_process_model_from_type(
            process_type=process_type, config_values=config_values, instance_name=instance_name)

    @classmethod
    def _init_process_model(
            cls, process_model: ProcessModel, config: Config, instance_name: str = None) -> None:

        process_model.status = ProcessStatus.DRAFT
        # Set the config
        process_model.config = config

        # Set the progress_bar
        progress_bar: ProgressBar = ProgressBar(
            process_uri=process_model.uri, process_typing_name=process_model.process_typing_name)
        process_model.progress_bar = progress_bar

        # set the created by
        user: User = CurrentUserService.get_current_user()

        if user is None:
            user = User.get_sysuser()
        process_model.created_by = user

        if instance_name is not None:
            process_model.instance_name = instance_name
        else:
            # Init the instance_name if it does not exists
            process_model.instance_name = process_model.uri
