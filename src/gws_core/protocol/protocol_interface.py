# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from inspect import isclass
from typing import List, Optional, Tuple, Type

from ..config.config_types import ConfigParamsDict
from ..io.port import InPort, OutPort
from ..process.process import Process
from ..process.process_interface import IProcess
from ..process.process_model import ProcessModel
from ..task.task import Task
from ..task.task_interface import ITask
from ..task.task_model import TaskModel
from .protocol import Protocol
from .protocol_model import ProtocolModel
from .protocol_service import ProtocolService


class IProtocol(IProcess):
    """This class can be used in a Jupyter Notebook to create and configure a protocol

    To create it use the add_protocol method on another protocol
    """

    _protocol_model: ProtocolModel

    def __init__(self, protocol_model: ProtocolModel, parent_protocol: Optional['IProtocol']) -> None:
        super().__init__(process_model=protocol_model, parent_protocol=parent_protocol)
        self._protocol_model = protocol_model

    def add_process(
            self, process_type: Type[Process],
            instance_name: str, config_params: ConfigParamsDict = None) -> IProcess:
        """Add a process (task or protocol) to this protocol. This process is automatically saved in the database"""

        # Check and create the process model
        if not isclass(process_type) or not issubclass(process_type, Process):
            raise Exception(f"The provided process_type '{str(process_type)}' is not a process")

        i_process: IProcess
        if issubclass(process_type, Task):
            i_process = self.add_task(process_type, instance_name, config_params)
        elif issubclass(process_type, Protocol):
            i_process = self.add_protocol(process_type, instance_name, config_params)

        return i_process

    def add_task(self, task_type: Type[Task], instance_name: str, config_params: ConfigParamsDict = None) -> ITask:
        """Add a task to this
        """
        task_model: TaskModel = ProtocolService.add_process_to_protocol(
            protocol_model=self._protocol_model, process_type=task_type, instance_name=instance_name,
            config_params=config_params)

        return ITask(task_model, self)

    def add_empty_protocol(self, instance_name: str) -> 'IProtocol':
        """Add an empty protocol to this protocol
        """
        protocol_model: ProcessModel = ProtocolService.add_empty_protocol_to_protocol(
            self._protocol_model, instance_name)
        return IProtocol(protocol_model, self)

    def add_protocol(self, protocol_type: Type[Protocol],
                     instance_name: str, config_params: ConfigParamsDict = None) -> 'IProtocol':
        """Add a protocol from a protocol type
        """
        protocol_model: ProtocolModel = ProtocolService.add_process_to_protocol(
            protocol_model=self._protocol_model, process_type=protocol_type,
            instance_name=instance_name, config_params=config_params)

        return IProtocol(protocol_model, self)

    def get_process(self, instance_name: str) -> IProcess:
        """retreive a protocol or a task in this protocol

        :param instance_name: [description]
        :type instance_name: str
        :raises Exception: [description]
        :return: [description]
        :rtype: IProcess
        """
        process: ProcessModel = self._protocol_model.get_process(instance_name)

        if isinstance(process, ProtocolModel):
            return IProtocol(process, self)
        else:
            return IProcess(process, self)

    def add_connector(self, out_port: OutPort, in_port: InPort) -> None:
        """Add a connector between to process of this protocol

        Exemple : protocol.add_connector(create >> 'robot', sub_proto << 'robot_i')
        """
        ProtocolService.add_connector_to_protocol(self._protocol_model, out_port, in_port)

    def add_connectors(self, connectors: List[Tuple[OutPort,  InPort]]) -> None:
        """Add multiple connector inside the protocol

        Exemple : protocol.add_connectors([
            (create >> 'robot', sub_proto << 'robot_i'),
            (sub_proto >> 'robot_o', robot_travel << 'robot')
        ])
        """
        ProtocolService.add_connectors_to_protocol(self._protocol_model, connectors)

    def add_interface(self, name: str, from_process: IProcess, process_input_name: str) -> None:
        """Add an interface to link an input of the protocol to the input of one of the protocol's process

        :param name: name of the interface
        :type name: str
        :param from_process: process that will be plugged to the interface
        :type from_process: IProcess
        :param process_input_name: name of the process input to plug
        :type process_input_name: str
        """
        port: InPort = from_process << process_input_name
        ProtocolService.add_interface_to_protocol(self._protocol_model, name, port)

    def add_outerface(self, name: str, to_process: IProcess, process_ouput_name: str) -> None:
        """Add an outerface to link the output of one of the protocol's process to the output of the protocol

        :param name: name of the interface
        :type name: str
        :param from_process: process that will be plugged to the interface
        :type from_process: IProcess
        :param process_ouput_name: name of the process output to plug
        :type process_ouput_name: str
        """
        port: OutPort = to_process >> process_ouput_name
        ProtocolService.add_outerface_to_protocol(self._protocol_model, name, port)
