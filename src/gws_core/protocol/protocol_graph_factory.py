

from typing import Dict, Literal, Type

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.model.typing_manager import TypingManager
from gws_core.process.process import Process
from gws_core.process.process_factory import ProcessFactory
from gws_core.process.process_model import ProcessModel
from gws_core.process.protocol_sub_process_builder import \
    ProtocolSubProcessBuilder
from gws_core.protocol.protocol import Protocol
from gws_core.protocol.protocol_dto import (ProcessConfigDTO,
                                            ProtocolGraphConfigDTO)
from gws_core.protocol.protocol_layout import ProtocolLayout
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.task.task import Task


class SubProcessBuilderCreate(ProtocolSubProcessBuilder):
    """Factory used to force creation of a processes when building a protocol
    It requires a ProtocolConfigDTO. It creates the process using the type of processes.
    For protocol, it creates an empty protocol.
    """

    protocol_config: ProtocolGraphConfigDTO

    def __init__(self, protocol_config: ProtocolGraphConfigDTO) -> None:
        super().__init__()
        self.protocol_config = protocol_config

    def instantiate_processes(self) -> Dict[str, ProcessModel]:
        processes: Dict[str, ProcessModel] = {}
        for instance_name, process_dto in self.protocol_config.nodes.items():
            processes[instance_name] = self.instantiate_process(instance_name, process_dto)
        return processes

    def instantiate_process(self, instance_name: str, process_dto: ProcessConfigDTO) -> ProcessModel:
        process_type_str: str = process_dto.process_typing_name
        process_type: Type[Process] = TypingManager.get_and_check_type_from_name(process_type_str)

        return self._create_new_process(process_type=process_type, instance_name=instance_name,
                                        process_dto=process_dto)

    def _create_new_process(self, process_type: Type[Process],
                            instance_name: str, process_dto: ProcessConfigDTO) -> ProcessModel:
        """Method to instantiate a new process and configure it
        """
        config_params: ConfigParamsDict = {}
        # Configure the process
        if process_dto.config:
            config_params = process_dto.config.values

        if issubclass(process_type, Task):
            return ProcessFactory.create_task_model_from_type(
                task_type=process_type, config_params=config_params, instance_name=instance_name,
                inputs_dto=process_dto.inputs if process_dto.inputs.type == 'dynamic' else None,
                outputs_dto=process_dto.outputs if process_dto.outputs.type == 'dynamic' else None, name=process_dto.
                name)
        elif issubclass(process_type, Protocol):
            # create an empty protocol, it will be filled with graph later
            return ProcessFactory.create_protocol_empty(instance_name, process_dto.name,
                                                        process_type)
        else:
            name = process_type.__name__ if process_type.__name__ is not None else str(
                process_type)
            raise BadRequestException(
                f"The type {name} is not a Process nor a Protocol. It must extend the on of the classes")


class SubProcessBuilderFromConfig(ProtocolSubProcessBuilder):
    """
    Factory used to force creation of a processes when building a protocol.
    Create the process from the ProcessConfigDTO without using the type of the process.
    It can create a process where the type does not exist in the system.
    """

    protocol_config: ProtocolGraphConfigDTO

    def __init__(self, protocol_config: ProtocolGraphConfigDTO) -> None:
        super().__init__()
        self.protocol_config = protocol_config

    def instantiate_processes(self) -> Dict[str, ProcessModel]:
        processes: Dict[str, ProcessModel] = {}
        for instance_name, process_dto in self.protocol_config.nodes.items():
            processes[instance_name] = self._create_new_process(process_dto)
        return processes

    def _create_new_process(self, process_dto: ProcessConfigDTO) -> ProcessModel:
        """Method to instantiate a new process and configure it
        """

        if process_dto.graph is None:
            return ProcessFactory.create_task_model_from_config_dto(process_dto)
        else:
            # create an empty protocol, it will be filled with graph later
            return ProcessFactory.create_empty_protocol_model_from_config_dto(process_dto)


class ProtocolGraphFactory():

    ############################################### PROTOCOL FROM GRAPH #################################################

    @classmethod
    def create_protocol_model_from_type(cls, graph: ProtocolGraphConfigDTO) -> ProtocolModel:
        """
        Create a new instance from a existing graph.
        It uses the type of the processes to create them and instantiate specs.

        :return: The protocol
        :rtype": Protocol
        """
        try:
            protocol: ProtocolModel = ProcessFactory.create_protocol_empty()

            return cls._create_protocol_model_from_graph_recur(protocol, graph, mode='type')
        except Exception as err:
            # log stacktrace
            Logger.log_exception_stack_trace(err)
            raise BadRequestException(
                f"The template is not compatible with the current version. {err}")

    @classmethod
    def create_protocol_model_from_config(cls, protocol_config_dto: ProcessConfigDTO) -> ProtocolModel:
        """
        Create a new instance from a existing graph.
        It uses only the config to create the processes and instantiate specs.

        :return: The protocol
        :rtype": Protocol
        """

        protocol: ProtocolModel = ProcessFactory.create_empty_protocol_model_from_config_dto(protocol_config_dto)

        return cls._create_protocol_model_from_graph_recur(protocol,
                                                           protocol_config_dto.graph,
                                                           mode='config')

    @classmethod
    def _create_protocol_model_from_graph_recur(cls, protocol: ProtocolModel,
                                                graph: ProtocolGraphConfigDTO,
                                                mode: Literal['type', 'config']) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        process_builder: ProtocolSubProcessBuilder = None

        if mode == 'type':
            process_builder = SubProcessBuilderCreate(graph)
        elif mode == 'config':
            process_builder = SubProcessBuilderFromConfig(graph)

        protocol.init_processes_from_graph(process_builder)

        # call the method recursively for each sub protocol
        for key, process in protocol.processes.items():
            if isinstance(process, ProtocolModel):
                cls._create_protocol_model_from_graph_recur(
                    protocol=process, graph=graph.nodes[key].graph, mode=mode)

        # Init the iofaces and connectors afterward because its needs the child to init correctly
        protocol.add_interfaces_from_dto(graph.interfaces)
        protocol.add_outerfaces_from_dto(graph.outerfaces)
        protocol.init_connectors_from_graph(graph.links)

        # set layout
        if graph.layout is not None:
            protocol.layout = ProtocolLayout(graph.layout)

        return protocol

    @classmethod
    def copy_protocol(cls, protocol_model: ProtocolModel) -> ProtocolModel:
        """Copy a protocol, copy sub nodes,copy interface, outerface and connecter

        :param protocol_model: [description]
        :type protocol_model: ProtocolModel
        :return: [description]
        :rtype: ProtocolModel
        """
        return cls.create_protocol_model_from_type(protocol_model.to_protocol_config_dto())
