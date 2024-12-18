

from abc import abstractmethod
from typing import Dict, Type

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
            # create protocol from dto, not from type
            return ProcessFactory.create_empty_protocol_model_from_config_dto(process_dto, copy_id=False)
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
    copy_id: bool

    def __init__(self, protocol_config: ProtocolGraphConfigDTO, copy_id: bool) -> None:
        super().__init__()
        self.protocol_config = protocol_config
        self.copy_id = copy_id

    def instantiate_processes(self) -> Dict[str, ProcessModel]:
        processes: Dict[str, ProcessModel] = {}
        for instance_name, process_dto in self.protocol_config.nodes.items():
            processes[instance_name] = self._create_new_process(process_dto)
        return processes

    def _create_new_process(self, process_dto: ProcessConfigDTO) -> ProcessModel:
        """Method to instantiate a new process and configure it
        """

        if process_dto.graph is None:
            return ProcessFactory.create_task_model_from_config_dto(process_dto, copy_id=self.copy_id)
        else:
            # create protocol from dto
            return ProcessFactory.create_empty_protocol_model_from_config_dto(process_dto, copy_id=self.copy_id)


class ProtocolGraphFactory():

    check_connector_compatiblity: bool

    def __init__(self, check_connector_compatiblity: bool) -> None:
        self.check_connector_compatiblity = check_connector_compatiblity

    @abstractmethod
    def create_sub_process_builder(self, protocol_config: ProtocolGraphConfigDTO) -> ProtocolSubProcessBuilder:
        pass

    @abstractmethod
    def create_protocol_model(self) -> ProtocolModel:
        pass

    def _create_protocol_model_from_graph_recur(self, protocol: ProtocolModel,
                                                graph: ProtocolGraphConfigDTO) -> ProtocolModel:
        """
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """

        process_builder: ProtocolSubProcessBuilder = self.create_sub_process_builder(graph)

        protocol.init_processes_from_graph(process_builder)

        # call the method recursively for each sub protocol
        for key, process in protocol.processes.items():
            if isinstance(process, ProtocolModel):
                self._create_protocol_model_from_graph_recur(
                    protocol=process, graph=graph.nodes[key].graph)

        # Init connectors afterward because its needs the child to init correctly
        protocol.init_connectors_from_graph(graph.links, check_compatiblity=self.check_connector_compatiblity)

        # set layout
        if graph.layout is not None:
            protocol.layout = ProtocolLayout(graph.layout)

        return protocol


class ProtocolGraphFactoryFromType(ProtocolGraphFactory):
    """
    Factory to create a protocol from a type.
    Create a new instance from a existing graph.
    It uses the type of the processes to create them and instantiate specs.
    """
    graph: ProtocolGraphConfigDTO

    def __init__(self, graph: ProtocolGraphConfigDTO):
        super().__init__(check_connector_compatiblity=True)
        self.graph = graph

    def create_sub_process_builder(self, protocol_config: ProtocolGraphConfigDTO) -> ProtocolSubProcessBuilder:
        return SubProcessBuilderCreate(protocol_config)

    def create_protocol_model(self) -> ProtocolModel:
        try:
            protocol: ProtocolModel = ProcessFactory.create_protocol_empty()

            return self._create_protocol_model_from_graph_recur(protocol, self.graph)
        except Exception as err:
            # log stacktrace
            Logger.log_exception_stack_trace(err)
            raise BadRequestException(
                f"The template is not compatible with the current version. {err}")


class ProtocolGraphFactoryFromConfig(ProtocolGraphFactory):
    """
    Factory to create a protocol from a config.
    Create a new instance from a existing graph.
    It uses only the config to create the processes and instantiate specs.

    """

    protocol_config_dto: ProcessConfigDTO
    copy_ids: bool

    def __init__(self, protocol_config_dto: ProcessConfigDTO, copy_ids: bool):
        # in the config mode, the process and resources types might not exist in the system
        # so we need to create the process from the config and not from the type
        # no need to check the connector compatibility because the process is created from the config
        super().__init__(check_connector_compatiblity=False)
        self.protocol_config_dto = protocol_config_dto
        self.copy_ids = copy_ids

    def create_sub_process_builder(self, protocol_config: ProtocolGraphConfigDTO) -> ProtocolSubProcessBuilder:
        return SubProcessBuilderFromConfig(protocol_config, self.copy_ids)

    def create_protocol_model(self) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_empty_protocol_model_from_config_dto(self.protocol_config_dto,
                                                                                             copy_id=self.copy_ids)

        return self._create_protocol_model_from_graph_recur(protocol,
                                                            self.protocol_config_dto.graph)
