

from typing import Dict, List, Optional, Type

from gws_core.io.io_dto import IODTO
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_dto import ProcessConfigDTO
from gws_core.protocol.protocol_spec import ConnectorSpec, InterfaceSpec
from gws_core.resource.view.viewer import Viewer
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask

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


class ProcessFactory():
    """Contains methods to instantiate TaskModel and ProtocolModel but it does not save the instances to the database,
    it only create th objects
    """

    ############################################### TASK #################################################

    @classmethod
    def create_task_model_from_type(
            cls, task_type: Type[Task],
            config_params: Optional[ConfigParamsDict] = None,
            instance_name: Optional[str] = None,
            inputs_dto: Optional[IODTO] = None,
            outputs_dto: Optional[IODTO] = None,
            name: Optional[str] = None,
            community_agent_version_id: Optional[str] = None,
            style: Optional[TypingStyle] = None) -> TaskModel:
        """
        Create a task model from a task type. The specs are created from the task type.

        :param task_type: _description_
        :type task_type: Type[Task]
        :param config_params: _description_, defaults to None
        :type config_params: Optional[ConfigParamsDict], optional
        :param instance_name: _description_, defaults to None
        :type instance_name: Optional[str], optional
        :param inputs_dto: If provided, override the input spec of the task (useful for dynamic IO), defaults to None
        :type inputs_dto: Optional[IODTO], optional
        :param outputs_dto: If provided, override the output spec of the task (useful for dynamic IO), defaults to None
        :type outputs_dto: Optional[IODTO], optional
        :param name: _description_, defaults to None
        :type name: Optional[str], optional
        :param community_agent_version_id: _description_, defaults to None
        :type community_agent_version_id: Optional[str], optional
        :param style: _description_, defaults to None
        :type style: Optional[TypingStyle], optional
        :raises BadRequestException: _description_
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: TaskModel
        """
        if not issubclass(task_type, Task):
            name = task_type.__name__ if task_type.__name__ is not None else str(
                task_type)
            raise BadRequestException(
                f"The type {name} is not a Task. It must extend the Task class")

        if not TypingManager.type_is_register(task_type):
            raise BadRequestException(
                f"The task {task_type.full_classname()} is not register. Did you add the @task_decorator decorator on your task class ?")

        task_model: TaskModel = TaskModel()
        task_model.set_process_type(task_type)

        # handle input and outputs
        if inputs_dto is not None:
            task_model.set_inputs_from_dto(inputs_dto, reset=True)
        else:
            task_model.set_inputs_from_specs(task_type.input_specs)

        if outputs_dto is not None:
            task_model.set_outputs_from_dto(outputs_dto, reset=True)
        else:
            task_model.set_outputs_from_specs(task_type.output_specs)

        # Set the community_agent_version_id if provided
        task_model.community_agent_version_id = community_agent_version_id

        config: Config = Config()
        config.set_specs(task_type.config_specs)
        if config_params:
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

    @classmethod
    def create_task_model_from_config_dto(cls, task_config_dto: ProcessConfigDTO) -> TaskModel:
        """Create a task model from a ProcessConfigDTO. The task is fully created from the dto and
        the process type is not used. It can create a task where the type does not exist in the system.

        :param task_config_dto: object containing the task configuration
        :type task_config_dto: ProcessConfigDTO
        :return: The task model
        :rtype: TaskModel
        """
        task_model: TaskModel = TaskModel()
        return cls._init_process_model_from_config_dto(task_model, task_config_dto)

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

            cls._init_process_model(
                process_model=protocol_model,
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

    @classmethod
    def create_empty_protocol_model_from_config_dto(cls, protocol_config_dto: ProcessConfigDTO) -> ProtocolModel:
        """Create a protocol model from a ProcessConfigDTO. The protocol is fully created from the dto and
        the process type is not used. It can create a protocol where the type does not exist in the system.

        Warning, it does not initialize the graph.
        :param task_config_dto: object containing the task configuration
        :type task_config_dto: ProcessConfigDTO
        :return: The task model
        :rtype: TaskModel
        """
        protocol_model: ProtocolModel = ProtocolModel()
        return cls._init_process_model_from_config_dto(protocol_model, protocol_config_dto)

    ############################################### PROTOCOL EMPTY #################################################

    @classmethod
    def create_protocol_empty(cls, instance_name: str = None, name: str = None,
                              protocol_type: Type[Protocol] = Protocol) -> ProtocolModel:

        protocol_model: ProtocolModel = ProtocolModel()

        # Use the Protocol default type because the protocol is not linked to a specific type
        protocol_model.set_process_type(protocol_type)

        cls._init_process_model(
            process_model=protocol_model,
            instance_name=instance_name, name=name)

        # create the protocol from a statis protocol class
        return protocol_model

    ############################################### PROCESS  #################################################

    @classmethod
    def create_process_model_from_type(
            cls, process_type: Type[Process],
            config_params: ConfigParamsDict = None,
            instance_name: str = None,
            community_agent_version_id: str = None) -> TaskModel:
        if issubclass(process_type, Task):
            return cls.create_task_model_from_type(
                process_type, config_params, instance_name,
                community_agent_version_id=community_agent_version_id)
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
    def _init_process_model_from_config_dto(cls, process_model: ProcessModel,
                                            process_config_dto: ProcessConfigDTO) -> ProcessModel:
        process_model.process_typing_name = process_config_dto.process_typing_name
        process_model.set_inputs_from_dto(process_config_dto.inputs)
        process_model.set_outputs_from_dto(process_config_dto.outputs)
        process_model.brick_version_on_create = process_config_dto.brick_version_on_create
        process_model.brick_version_on_run = process_config_dto.brick_version_on_run

        cls._init_process_model(process_model=process_model,
                                config=Config.from_simple_dto(process_config_dto.config),
                                status=ProcessStatus.from_str(process_config_dto.status),
                                instance_name=process_config_dto.instance_name,
                                name=process_config_dto.name,
                                style=process_config_dto.style,
                                progress_bar=ProgressBar.from_config_dto(process_config_dto.progress_bar))

        return process_model

    @classmethod
    def _init_process_model(cls, process_model: ProcessModel,
                            config: Optional[Config] = None,
                            status: Optional[ProcessStatus] = None,
                            instance_name: Optional[str] = None,
                            name: Optional[str] = None,
                            style: Optional[TypingStyle] = None,
                            progress_bar: Optional[ProgressBar] = None) -> None:

        if status is not None:
            process_model.status = status
        else:
            process_model.status = ProcessStatus.DRAFT

        # Set the config
        if config is not None:
            process_model.set_config(config)
        else:
            process_model.set_config(Config())

        # Set the progress_bar
        if progress_bar is not None:
            progress_bar.process_id = process_model.id
            progress_bar.process_typing_name = process_model.process_typing_name
            process_model.progress_bar = progress_bar
        else:
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

    ############################################### SPECIFIC #################################################

    @classmethod
    def create_source(cls, resouce_id: str) -> TaskModel:
        return cls.create_task_model_from_type(InputTask, {InputTask.config_name: resouce_id})

    @classmethod
    def create_output_task(cls) -> TaskModel:
        return cls.create_task_model_from_type(OutputTask)

    @classmethod
    def create_viewer(cls, resource_typing_name: str) -> TaskModel:
        return cls.create_task_model_from_type(Viewer, {Viewer.resource_config_name: resource_typing_name})
