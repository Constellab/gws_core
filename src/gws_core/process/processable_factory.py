

from typing import Type

from ..config.config import Config
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..io.connector import Connector
from ..model.typing_manager import TypingManager
from ..process.process import Process
from ..process.process_model import ProcessModel
from ..process.processable import Processable
from ..process.processable_model import ProcessableModel
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import (CONST_PROTOCOL_TYPING_NAME, Protocol,
                                 ProtocolCreateConfig)
from ..protocol.protocol_model import ProtocolModel
from ..protocol.sub_processable_factory import SubProcessFactoryCreate
from ..user.current_user_service import CurrentUserService
from ..user.user import User


class ProcessableFactory():
    """Contains methods to instantiate ProcessModel and ProtocolModel but it does not save the instances to the database,
    it only create th objects
    """

    @classmethod
    def create_processable_from_type(
            cls, processable_type: Type[Processable],
            instance_name: str = None) -> ProcessModel:
        if issubclass(processable_type, Process):
            return cls.create_process_from_type(processable_type, instance_name)
        elif issubclass(processable_type, Protocol):
            return cls.create_protocol_from_type(processable_type, instance_name)
        else:
            name = processable_type.__name__ if processable_type.__name__ is not None else str(
                processable_type)
            raise BadRequestException(
                f"The type {name} is not a Process nor a Protocol. It must extend the on of the classes")

    @classmethod
    def create_process_from_type(cls, process_type: Type[Process], instance_name: str = None) -> ProcessModel:
        if not issubclass(process_type, Process):
            name = process_type.__name__ if process_type.__name__ is not None else str(
                process_type)
            raise BadRequestException(
                f"The type {name} is not a Process. It must extend the Process class")

        if not TypingManager.type_is_register(process_type):
            raise BadRequestException(
                f"The process {process_type.full_classname()} is not register. Did you add the @ProcessDecorator decorator on your process class ?")

        process_model: ProcessModel = ProcessModel(process_type)
        process_model.set_process_type(process_type)

        cls._init_processable(processable_model=process_model,
                              config=Config(specs=process_type.config_specs), instance_name=instance_name)

        return process_model

    @classmethod
    def create_process_from_typing_name(cls, typing_name: str, instance_name: str = None) -> ProcessModel:
        return cls.create_process_from_type(
            TypingManager.get_type_from_name(typing_name=typing_name),
            instance_name=instance_name)

    @classmethod
    def create_protocol_from_type(cls, protocol_type: Type[Protocol], instance_name: str = None) -> ProtocolModel:
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

        cls._init_processable(processable_model=protocol_model,
                              config=Config(specs=protocol_type.config_specs), instance_name=instance_name)

        protocol: Protocol = protocol_type()

        create_config: ProtocolCreateConfig = protocol.get_create_config()
        # create the protocol from a statis protocol class
        return cls._build_protocol(
            protocol=protocol_model,
            processes=create_config["processes"],
            connectors=create_config["connectors"],
            interfaces=create_config["interfaces"],
            outerfaces=create_config["outerfaces"]
        )

    @classmethod
    def create_protocol_from_data(cls, processes: dict = None,
                                  connectors: list = None,
                                  interfaces: dict = None,
                                  outerfaces: dict = None,
                                  instance_name: str = None) -> ProtocolModel:
        protocol_model: ProtocolModel = ProtocolModel()

        # Use the Protocol default type because the protocol is not linked to a specific type
        protocol_model.processable_typing_name = CONST_PROTOCOL_TYPING_NAME

        cls._init_processable(
            processable_model=protocol_model, config=Config({}), instance_name=instance_name)

        # create the protocol from a statis protocol class
        return cls._build_protocol(
            protocol=protocol_model,
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
        )

    @classmethod
    def _build_protocol(cls, protocol: ProtocolModel, processes: dict = None,
                        connectors: list = None,
                        interfaces: dict = None,
                        outerfaces: dict = None) -> ProtocolModel:
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
            protocol.add_process(name, proc)

        # set connectors
        for conn in connectors:
            if not isinstance(conn, Connector):
                raise BadRequestException(
                    "The list of connector must contain instances of Connectors")
            protocol.add_connector(conn)

        # set interfaces
        protocol.set_interfaces(interfaces)
        protocol.set_outerfaces(outerfaces)
        protocol.data["graph"] = protocol.dumps()

        return protocol

    @classmethod
    def create_protocol_from_graph(cls, graph: dict) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        # create an empty protocol
        protocol: ProtocolModel = cls.create_protocol_from_type(
            protocol_type=Protocol)

        cls._create_protocol_from_graph_recur(protocol=protocol, graph=graph)
        return protocol

    @classmethod
    def _create_protocol_from_graph_recur(cls, protocol: ProtocolModel, graph: dict) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        protocol.build_from_graph(
            graph=graph, sub_processable_factory=SubProcessFactoryCreate())

        for key, processable in protocol.processes.items():
            if isinstance(processable, ProtocolModel):
                cls._create_protocol_from_graph_recur(
                    protocol=processable, graph=graph["nodes"][key]["data"]["graph"])

        return protocol

    @classmethod
    def _init_processable(cls, processable_model: ProcessableModel, config: Config, instance_name: str = None) -> None:
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
