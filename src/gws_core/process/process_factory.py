

from typing import Dict, List, Type

from gws_core.core.utils.logger import Logger
from gws_core.io.io_dto import IODTO
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_dto import ProtocolConfigDTO
from gws_core.protocol.protocol_layout import ProtocolLayout
from gws_core.protocol.protocol_spec import ConnectorSpec, InterfaceSpec
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.viewer import Viewer
from gws_core.task.plug import Sink, Source

from ..config.config import Config
from ..config.config_types import ConfigParamsDict
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import Protocol, ProtocolCreateConfig
from ..protocol.protocol_exception import ProtocolBuildException
from ..protocol.protocol_model import ProtocolModel
from ..task.task import Task
from ..task.task_model import TaskModel
from .process import Process
from .process_model import ProcessModel
from .process_types import ProcessStatus
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
            instance_name: str = None,
            inputs_dto: IODTO = None,
            outputs_dto: IODTO = None,
            name: str = None,
            community_live_task_version_id: str = None,
            style: TypingStyle = None) -> TaskModel:
        if not issubclass(task_type, Task):
            name = task_type.__name__ if task_type.__name__ is not None else str(
                task_type)
            raise BadRequestException(
                f"The type {name} is not a Task. It must extend the Task class")

        if not TypingManager.type_is_register(task_type):
            raise BadRequestException(
                f"The task {task_type.full_classname()} is not register. Did you add the @task_decorator decorator on your task class ?")

        task_model: TaskModel = TaskModel()
        task_model.set_process_type(task_type, inputs_dto, outputs_dto)

        # Set the community_live_task_version_id if provided
        task_model.community_live_task_version_id = community_live_task_version_id

        config: Config = Config()
        config.set_specs(task_type.config_specs)
        if config_params:
            # Specific case for the source, to set the source_config id is provided
            if task_type == Source and config_params.get(Source.config_name):
                # check if the resource exists
                resource_id: str = config_params.get(Source.config_name)
                if ResourceModel.get_by_id(resource_id):
                    task_model.source_config_id = config_params.get(
                        Source.config_name)
                else:
                    # clear the resource_id
                    config_params[Source.config_name] = None

            config.set_values(config_params)

        cls._init_process_model(process_model=task_model,
                                config=config,
                                instance_name=instance_name,
                                name=name, style=style)

        return task_model

    @classmethod
    def create_task_model_from_typing_name(
            cls, typing_name: str, config_params: ConfigParamsDict = None, instance_name: str = None) -> TaskModel:
        task_type: Type[Task] = TypingManager.get_and_check_type_from_name(
            typing_name=typing_name)
        return cls.create_task_model_from_type(
            task_type=task_type, config_params=config_params, instance_name=instance_name)

    ############################################### PROTOCOL FROM TYPE #################################################

    @classmethod
    def create_protocol_model_from_type(cls, protocol_type: Type[Protocol],
                                        config_params: ConfigParamsDict = None,
                                        instance_name: str = None,
                                        name: str = None) -> ProtocolModel:

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
            protocol_model.set_process_type(protocol_type)

            config: Config = Config()
            cls._init_process_model(
                process_model=protocol_model, config=config,
                instance_name=instance_name, name=name)

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
                    raise ProtocolBuildException.from_exception(
                        'Task', key, err)

            # create the protocol from a statis protocol class
            return cls._build_protocol_model_from_type(
                protocol_model=protocol_model,
                processes=processes,
                connectors=create_config["connectors"],
                interfaces=create_config["interfaces"],
                outerfaces=create_config["outerfaces"]
            )
        except ProtocolBuildException as err:
            raise ProtocolBuildException.from_build_exception(
                parent_instance_name=instance_name, exception=err)
        except Exception as err:
            raise ProtocolBuildException.from_exception(
                'Protocol', instance_name, err)

    @classmethod
    def _build_protocol_model_from_type(cls, protocol_model: ProtocolModel, processes: Dict[str, ProcessModel] = None,
                                        connectors: List[ConnectorSpec] = None,
                                        interfaces: Dict[str, InterfaceSpec] = None,
                                        outerfaces: Dict[str, InterfaceSpec] = None) -> ProtocolModel:
        """Construct the protocol graph from the attribut of Protocol class
        """
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
        protocol_model.add_connectors(connectors)

        # set interfaces and outerfaces
        protocol_model.add_interfaces(interfaces)
        protocol_model.add_outerfaces(outerfaces)

        # refresh the json graph
        protocol_model.refresh_graph_from_dump()

        return protocol_model

    ############################################### PROTOCOL FROM GRAPH #################################################

    @classmethod
    def create_protocol_model_from_graph(cls, graph: ProtocolConfigDTO) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        # create an empty protocol
        protocol: ProtocolModel = cls.create_protocol_empty()

        cls._create_protocol_model_from_graph_recur(
            protocol=protocol, graph=graph)
        return protocol

    @classmethod
    def _create_protocol_model_from_graph_recur(cls, protocol: ProtocolModel,
                                                graph: ProtocolConfigDTO) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        protocol.init_processes_from_graph(SubProcessBuilderCreate(graph))

        # call the method recursively for each sub protocol
        for key, process in protocol.processes.items():
            if isinstance(process, ProtocolModel):
                cls._create_protocol_model_from_graph_recur(
                    protocol=process, graph=graph.nodes[key].graph)

        # Init the iofaces and connectors afterward because its needs the child to init correctly
        protocol.add_interfaces_from_dto(graph.interfaces)
        protocol.add_outerfaces_from_dto(graph.outerfaces)
        protocol.init_connectors_from_graph(graph.links)

        # set layout
        if graph.layout is not None:
            protocol.layout = ProtocolLayout(graph.layout)

        return protocol

    ############################################### PROTOCOL EMPTY #################################################

    @classmethod
    def create_protocol_empty(cls, instance_name: str = None, name: str = None,
                              protocol_type: Type[Protocol] = Protocol) -> ProtocolModel:

        protocol_model: ProtocolModel = ProtocolModel()

        # Use the Protocol default type because the protocol is not linked to a specific type
        protocol_model.set_process_type(protocol_type)

        cls._init_process_model(
            process_model=protocol_model, config=Config(),
            instance_name=instance_name, name=name)

        # create the protocol from a statis protocol class
        return protocol_model

    ############################################### PROCESS  #################################################

    @classmethod
    def create_process_model_from_type(
            cls, process_type: Type[Process],
            config_params: ConfigParamsDict = None,
            instance_name: str = None,
            community_live_task_version_id: str = None) -> TaskModel:
        if issubclass(process_type, Task):
            return cls.create_task_model_from_type(
                process_type, config_params, instance_name,
                community_live_task_version_id=community_live_task_version_id)
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
        process_type: Type[Process] = TypingManager.get_and_check_type_from_name(
            typing_name=typing_name)
        return cls.create_process_model_from_type(
            process_type=process_type, config_params=config_params, instance_name=instance_name)

    @classmethod
    def create_process_model_from_process_model(
            cls, process_model: ProcessModel, instance_name: str = None) -> ProcessModel:
        if isinstance(process_model, TaskModel):
            return cls.create_task_model_from_type(
                process_model.get_process_type(), process_model.config.get_values(), instance_name)
        else:
            return cls.create_protocol_model_from_graph(process_model.to_protocol_config_dto())

    @classmethod
    def _init_process_model(
            cls, process_model: ProcessModel, config: Config,
            instance_name: str = None, name: str = None,
            style: TypingStyle = None) -> None:

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

        if name is not None:
            process_model.name = name

        if style is not None:
            process_model.style = style

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
        return cls.create_protocol_model_from_graph(protocol_model.to_protocol_config_dto())

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
