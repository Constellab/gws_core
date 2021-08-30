

from logging import exception
from typing import Dict, List, Type

from ..config.config import Config
from ..config.config_spec import ConfigValues
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.connector import Connector
from ..io.port import Port
from ..model.typing_manager import TypingManager
from ..process.process import Process
from ..process.process_model import ProcessModel
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import (CONST_PROTOCOL_TYPING_NAME, Protocol,
                                 ProtocolCreateConfig)
from ..protocol.protocol_exception import ProtocolBuildException
from ..protocol.protocol_model import ProtocolModel
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .processable import Processable
from .processable_model import ProcessableModel
from .sub_processable_factory import SubProcessFactoryCreate


class ProcessableFactory():
    """Contains methods to instantiate ProcessModel and ProtocolModel but it does not save the instances to the database,
    it only create th objects
    """

    ############################################### PROCESS #################################################

    @classmethod
    def create_process_model_from_type(
            cls, process_type: Type[Process],
            config_values: ConfigValues = None,
            instance_name: str = None) -> ProcessModel:
        if not issubclass(process_type, Process):
            name = process_type.__name__ if process_type.__name__ is not None else str(
                process_type)
            raise BadRequestException(
                f"The type {name} is not a Process. It must extend the Process class")

        if not TypingManager.type_is_register(process_type):
            raise BadRequestException(
                f"The process {process_type.full_classname()} is not register. Did you add the @ProcessDecorator decorator on your process class ?")

        process_model: ProcessModel = ProcessModel()
        process_model.set_process_type(process_type._typing_name)

        config: Config = Config(specs=process_type.config_specs)
        if config_values:
            config.set_params(config_values)

        cls._init_processable_model(processable_model=process_model, config=config, instance_name=instance_name)

        return process_model

    @classmethod
    def create_process_model_from_typing_name(
            cls, typing_name: str, config_values: ConfigValues = None, instance_name: str = None) -> ProcessModel:
        process_type: Type[Process] = TypingManager.get_type_from_name(typing_name=typing_name)
        return cls.create_process_model_from_type(
            process_type=process_type, config_values=config_values, instance_name=instance_name)

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

            cls._init_processable_model(processable_model=protocol_model, config=config, instance_name=instance_name)

            protocol: Protocol = protocol_type()
            protocol.configure_protocol(config.get_and_check_params())
            create_config: ProtocolCreateConfig = protocol.get_create_config()

            # Create the process and protocol (recursive)
            processes: Dict[str, ProcessableModel] = {}
            for key, proc in create_config["processable_specs"].items():
                try:
                    processes[key] = ProcessableFactory.create_processable_model_from_type(
                        proc.processable_type, proc.get_config_values(), proc.instance_name)
                except ProtocolBuildException as err:
                    raise err
                except Exception as err:
                    raise ProtocolBuildException.from_exception('Process', key, err)

            # Set the protocol interfaces
            interfaces: Dict[str, Port] = {}
            for key, interface in create_config["interfaces"].items():
                interfaces[key] = processes[interface["processable_instance_name"]].in_port(interface["port_name"])

            # Set the protocol outerfaces
            outerfaces: Dict[str, Port] = {}
            for key, outerface in create_config["outerfaces"].items():
                outerfaces[key] = processes[outerface["processable_instance_name"]].out_port(outerface["port_name"])

            # Set the connectors
            connectors: List[Connector] = []
            for connector in create_config["connectors"]:
                from_proc: ProcessableModel = processes[connector["from_processable"]]
                to_proc: ProcessableModel = processes[connector["to_processable"]]
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
    def create_protocol_model_from_data(cls, processes: Dict[str, ProcessableModel] = None,
                                        connectors: List[Connector] = None,
                                        interfaces: Dict[str, Port] = None,
                                        outerfaces: Dict[str, Port] = None,
                                        instance_name: str = None) -> ProtocolModel:
        protocol_model: ProtocolModel = ProtocolModel()

        # Use the Protocol default type because the protocol is not linked to a specific type
        protocol_model.processable_typing_name = CONST_PROTOCOL_TYPING_NAME

        cls._init_processable_model(
            processable_model=protocol_model, config=Config({}), instance_name=instance_name)

        # create the protocol from a statis protocol class
        return cls._build_protocol_model(
            protocol_model=protocol_model,
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
        )

    @classmethod
    def _build_protocol_model(cls, protocol_model: ProtocolModel, processes: Dict[str, ProcessableModel] = None,
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
            if not isinstance(proc, ProcessableModel):
                raise BadRequestException(
                    "The dictionnary of processes must contain instances of ProcessableModel")
            protocol_model.add_process(name, proc)

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
            graph=graph, sub_processable_factory=SubProcessFactoryCreate())

        for key, processable in protocol.processes.items():
            if isinstance(processable, ProtocolModel):
                cls._create_protocol_model_from_graph_recur(
                    protocol=processable, graph=graph["nodes"][key]["data"]["graph"])

        # Init the connector afterward because its needs the child to init correctly
        protocol.init_connectors_from_graph(graph["links"])

        return protocol

    ############################################### PROCESSABLE #################################################

    @classmethod
    def create_processable_model_from_type(
            cls, processable_type: Type[Processable],
            config_values: ConfigValues = None,
            instance_name: str = None) -> ProcessModel:
        if issubclass(processable_type, Process):
            return cls.create_process_model_from_type(processable_type, config_values, instance_name)
        elif issubclass(processable_type, Protocol):
            return cls.create_protocol_model_from_type(processable_type, config_values, instance_name)
        else:
            name = processable_type.__name__ if processable_type.__name__ is not None else str(
                processable_type)
            raise BadRequestException(
                f"The type {name} is not a Process nor a Protocol. It must extend the on of the classes")

    @classmethod
    def _init_processable_model(
            cls, processable_model: ProcessableModel, config: Config, instance_name: str = None) -> None:

        # Set the config
        processable_model.config = config

        # Set the progress_bar
        progress_bar: ProgressBar = ProgressBar(
            process_uri=processable_model.uri, processable_typing_name=processable_model.processable_typing_name)
        processable_model.progress_bar = progress_bar

        # set the created by
        user: User = CurrentUserService.get_current_user()

        if user is None:
            user = User.get_sysuser()
        processable_model.created_by = user

        if instance_name is not None:
            processable_model.instance_name = instance_name
        else:
            # Init the instance_name if it does not exists
            processable_model.instance_name = processable_model.uri
