

from inspect import isclass
from typing import List, Tuple, Type

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.protocol.protocol_spec import ConnectorSpec
from gws_core.protocol.protocol_update import ProtocolUpdate
from gws_core.task.plug import InputTask, OutputTask

from ..config.config_types import ConfigParamsDict
from ..config.param.param_types import ParamValue
from ..process.process import Process
from ..process.process_model import ProcessModel
from ..process.process_proxy import ProcessProxy, ProcessWithPort
from ..task.task import Task
from ..task.task_proxy import TaskProxy
from .protocol import Protocol
from .protocol_model import ProtocolModel
from .protocol_service import ProtocolService


class ProtocolProxy(ProcessProxy):
    """This class can be used in a Jupyter Notebook to create and configure a protocol

    To create it use the add_protocol method on another protocol
    """

    _process_model: ProtocolModel

    def __init__(self, protocol_model: ProtocolModel) -> None:
        super().__init__(process_model=protocol_model)
        self._process_model = protocol_model

    def get_model(self) -> ProtocolModel:
        return self._process_model

    ####################################### PROCESS #########################################

    def add_process(
            self, process_type: Type[Process],
            instance_name: str, config_params: ConfigParamsDict = None) -> ProcessProxy:
        """Add a process (task or protocol) to this protocol. This process is automatically saved in the database"""

        # Check and create the process model
        if not isclass(process_type) or not issubclass(process_type, Process):
            raise Exception(
                f"The provided process_type '{str(process_type)}' is not a process")

        i_process: ProcessProxy
        if issubclass(process_type, Task):
            i_process = self.add_task(
                process_type, instance_name, config_params)
        elif issubclass(process_type, Protocol):
            i_process = self.add_protocol(
                process_type, instance_name, config_params)

        return i_process

    def add_task(self, task_type: Type[Task], instance_name: str, config_params: ConfigParamsDict = None) -> TaskProxy:
        """Add a task to this
        """
        protocol_update: ProtocolUpdate = ProtocolService.add_process_to_protocol(
            protocol_model=self._process_model, process_type=task_type, instance_name=instance_name,
            config_params=config_params)

        return TaskProxy(protocol_update.process)

    def add_empty_protocol(self, instance_name: str) -> 'ProtocolProxy':
        """Add an empty protocol to this protocol
        """
        protocol_update: ProtocolUpdate = ProtocolService.add_empty_protocol_to_protocol(
            self._process_model, instance_name)
        return ProtocolProxy(protocol_update.process)

    def add_protocol(self, protocol_type: Type[Protocol],
                     instance_name: str, config_params: ConfigParamsDict = None) -> 'ProtocolProxy':
        """Add a protocol from a protocol type
        """
        protocol_update: ProtocolUpdate = ProtocolService.add_process_to_protocol(
            protocol_model=self._process_model, process_type=protocol_type,
            instance_name=instance_name, config_params=config_params)

        return ProtocolProxy(protocol_update.process)

    def get_process(self, instance_name: str) -> ProcessProxy:
        """retreive a protocol or a task in this protocol

        :param instance_name: [description]
        :type instance_name: str
        :raises Exception: [description]
        :return: [description]
        :rtype: IProcess
        """
        process: ProcessModel = self._process_model.get_process(instance_name)

        if isinstance(process, ProtocolModel):
            return ProtocolProxy(process)
        else:
            return TaskProxy(process)

    def delete_process(self, instance_name: str) -> None:
        ProtocolService.delete_process_of_protocol(
            self._process_model, instance_name)

    ####################################### CONNECTORS #########################################

    def add_connector(self, out_port: ProcessWithPort, in_port: ProcessWithPort) -> None:
        """Add a connector between to process of this protocol

        Exemple :
        protocol.add_connector(create.get_output_port('robot'), sub_proto.get_input_port('robot_i'))
        OR
        protocol.add_connector(create >> 'robot', sub_proto << 'robot_i')
        """
        self.add_connector_new(
            out_port.process_instance_name, out_port.port_name, in_port.process_instance_name, in_port.port_name)

    def add_connector_new(self, from_process_name: str, from_port_name: str,
                          to_process_name: str, to_port_name: str) -> None:
        """Add a connector between to process of this protocol

        Exemple : protocol.add_connector('create', 'robot', 'sub_proto','robot_i')
        """

        ProtocolService.add_connector_to_protocol(self._process_model, from_process_name, from_port_name,
                                                  to_process_name, to_port_name)

    def add_connectors(self, connectors: List[Tuple[ProcessWithPort,  ProcessWithPort]]) -> None:
        """Add multiple connector inside the protocol

        Exemple : protocol.add_connectors([
            (create >> 'robot', sub_proto << 'robot_i'),
            (sub_proto.get_output_port('robot_o'), robot_travel.get_input_port('robot'))
        ])
        """
        new_connectors: List[ConnectorSpec] = []
        for connector in connectors:
            new_connectors.append({
                "from_process": connector[0].process_instance_name, "to_process": connector[1].process_instance_name,
                "from_port": connector[0].port_name, "to_port": connector[1].port_name})

        ProtocolService.add_connectors_to_protocol(
            self._process_model, new_connectors)

    ####################################### INTERFACE & OUTERFACE #########################################

    def add_interface(self, name: str, from_process_name: str, process_input_name: str) -> None:
        """Add an interface to link an input of the protocol to the input of one of the protocol's process

        :param name: name of the interface
        :type name: str
        :param from_process: process that will be plugged to the interface
        :type from_process: IProcess
        :param process_input_name: name of the process input to plug
        :type process_input_name: str
        """
        ProtocolService.add_interface_to_protocol(
            self._process_model, name, from_process_name, process_input_name)

    def add_outerface(self, name: str, to_process_name: str, process_ouput_name: str) -> None:
        """Add an outerface to link the output of one of the protocol's process to the output of the protocol

        :param name: name of the interface
        :type name: str
        :param from_process: process that will be plugged to the interface
        :type from_process: IProcess
        :param process_ouput_name: name of the process output to plug
        :type process_ouput_name: str
        """
        ProtocolService.add_outerface_to_protocol(
            self._process_model, name, to_process_name, process_ouput_name)

    def delete_interface(self, name: str) -> None:
        """Delete an interface of the protocol
        """
        ProtocolService.delete_interface_of_protocol(self._process_model, name)

    def delete_outerface(self, name: str) -> None:
        """Delete an outerface of the protocol
        """
        ProtocolService.delete_outerface_of_protocol(self._process_model, name)

    ############################################### Config ####################################
    # Block config of the protocol because it does not transfer the config to the task

    def set_param(self, param_name: str, value: ParamValue) -> None:
        """Set the param value
        """
        raise BadRequestException(
            "The configuration of protocol is not available yet. Please configure the sub task directly")

    def set_config_params(self, config_params: ConfigParamsDict) -> None:
        """Set the config param values
        """
        raise BadRequestException(
            "The configuration of protocol is not available yet. Please configure the sub task directly")

    ############################################### Specific processes ####################################

    def add_resource(
            self, instance_name: str, resource_model_id: str, in_port: ProcessWithPort = None) -> TaskProxy:
        """Add a resource to the protocol and connected it to the in_port
        :param instance_name: instance name of the task
        :type instance_name: str
        :param resource_model_id: the id of the resource model the source will provided as input
        :type resource_model_id: str
        :param in_port: the in port that should receive the resource. If None, the resource is added to the protocol without connection
        :type in_port: InPort
        :return: [description]
        :rtype: ITask
        """
        config = {InputTask.config_name: resource_model_id} if resource_model_id else {}
        source: ProcessProxy = self.add_process(
            InputTask, instance_name, config)

        if in_port:
            self.add_connector(source >> InputTask.output_name, in_port)
        return source

    def add_source(self, instance_name: str, resource_model_id: str, in_port: ProcessWithPort) -> TaskProxy:
        """Add a Source task to the protocol and connected it to the in_port
        :param instance_name: instance name of the task
        :type instance_name: str
        :param resource_model_id: the id of the resource model the source will provided as input
        :type resource_model_id: str
        :param in_port: the in port that should receive the resource
        :type in_port: InPort
        :return: [description]
        :rtype: ITask
        """
        Logger.warning(
            "The add_source method is deprecated, please use add_resource instead")
        return self.add_resource(instance_name, resource_model_id, in_port)

    def add_output(
            self, instance_name: str, out_port: ProcessWithPort,
            flag_resource: bool = True) -> TaskProxy:
        """Add an output task to the protocol that receive the out_port resource

        :param instance_name: instance name of the task
        :type instance_name: str
        :param out_port: out_port connect to connect to the output task
        :type out_port: OutPort
        :param flag_resource: flag the resource, defaults to True
        :type flag_resource: bool, optional
        :return: [description]
        :rtype: ITask
        """
        output_task = self.add_process(OutputTask, instance_name, {OutputTask.flag_config_name: flag_resource})
        self.add_connector(out_port, output_task << OutputTask.input_name)
        return output_task

    # TODO v0.11.0 to remove
    def add_sink(self, instance_name: str, out_port: ProcessWithPort,
                 flag_resource: bool = True) -> TaskProxy:
        """Add an output task to the protocol that receive the out_port resource

        :param instance_name: instance name of the task
        :type instance_name: str
        :param out_port: out_port connect to connect to the output task
        :type out_port: OutPort
        :param flag_resource: flag the resource, defaults to True
        :type flag_resource: bool, optional
        :return: [description]
        :rtype: ITask
        """
        Logger.warning(
            "The add_sink method is deprecated, please use add_output instead")
        return self.add_output(instance_name, out_port, flag_resource)

    ############################################### CLASS METHODS ####################################

    @classmethod
    def get_by_id(cls, id: str) -> 'ProtocolProxy':
        protocol_model: ProtocolModel = ProtocolService.get_by_id_and_check(id)
        return ProtocolProxy(protocol_model)
