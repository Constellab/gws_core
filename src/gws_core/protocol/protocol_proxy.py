from inspect import isclass

from gws_core.config.config_params import ConfigParamsDict
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.io.io_spec import IOSpecDTO
from gws_core.protocol.protocol_spec import ConnectorSpec
from gws_core.protocol.protocol_update import ProtocolUpdate
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask

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
        self,
        process_type: type[Process],
        instance_name: str | None = None,
        config_params: ConfigParamsDict = None,
    ) -> ProcessProxy:
        """Add a process (task or protocol) to this protocol. This process is automatically saved in the database"""

        # Check and create the process model
        if not isclass(process_type) or not issubclass(process_type, Process):
            raise Exception(f"The provided process_type '{str(process_type)}' is not a process")

        i_process: ProcessProxy
        if issubclass(process_type, Task):
            i_process = self.add_task(process_type, instance_name, config_params)
        elif issubclass(process_type, Protocol):
            i_process = self.add_protocol(process_type, instance_name, config_params)

        return i_process

    def add_task(
        self,
        task_type: type[Task],
        instance_name: str | None = None,
        config_params: ConfigParamsDict = None,
    ) -> TaskProxy:
        """Add a task to this"""
        protocol_update: ProtocolUpdate = ProtocolService.add_process_to_protocol(
            protocol_model=self._process_model,
            process_type=task_type,
            instance_name=instance_name,
            config_params=config_params,
        )

        return TaskProxy(protocol_update.process)

    def add_empty_protocol(self, instance_name: str | None = None) -> "ProtocolProxy":
        """Add an empty protocol to this protocol"""
        protocol_update: ProtocolUpdate = ProtocolService.add_empty_protocol_to_protocol(
            self._process_model, instance_name
        )
        return ProtocolProxy(protocol_update.process)

    def add_protocol(
        self,
        protocol_type: type[Protocol],
        instance_name: str | None = None,
        config_params: ConfigParamsDict = None,
    ) -> "ProtocolProxy":
        """Add a protocol from a protocol type"""
        protocol_update: ProtocolUpdate = ProtocolService.add_process_to_protocol(
            protocol_model=self._process_model,
            process_type=protocol_type,
            instance_name=instance_name,
            config_params=config_params,
        )

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

    def get_processes_by_type(self, process_type: type[Process]) -> list[ProcessProxy]:
        """retreive a protocol or a task in this protocol by type

        :param process_type: [description]
        :type process_type: type[Process]
        :raises Exception: [description]
        :return: [description]
        :rtype: list[ProcessProxy]
        """
        if not isclass(process_type) or not issubclass(process_type, Process):
            raise BadRequestException(
                f"Invalid process_type '{process_type}'. Expected a subclass of Process."
            )
        processes: list[ProcessModel] = self._process_model.get_processes_by_type(process_type)

        process_proxies: list[ProcessProxy] = []
        for process in processes:
            if isinstance(process, ProtocolModel):
                process_proxies.append(ProtocolProxy(process))
            else:
                process_proxies.append(TaskProxy(process))

        return process_proxies

    def delete_process(self, instance_name: str) -> None:
        ProtocolService.delete_process_of_protocol(self._process_model, instance_name)

    def get_direct_next_processes(self, instance_name: str) -> set[ProcessProxy]:
        """Return the direct next processes of the specified process in this protocol

        :param instance_name: the instance name of the process
        :type instance_name: str
        :return: the list of direct next processes
        :rtype: List[IProcess]
        """
        next_process_models = self._process_model.get_direct_next_processes(instance_name)

        return self._get_process_proxies(next_process_models)

    def get_direct_previous_processes(self, instance_name: str) -> set[ProcessProxy]:
        """Return the direct previous processes of the specified process in this protocol

        :param instance_name: the instance name of the process
        :type instance_name: str
        :return: the list of direct previous processes
        :rtype: List[IProcess]
        """
        previous_process_models = self._process_model.get_direct_previous_processes(instance_name)

        return self._get_process_proxies(previous_process_models)

    def get_all_next_processes(self, instance_name: str) -> set[ProcessProxy]:
        """Return all the next processes of the specified process in this protocol

        :param instance_name: the instance name of the process
        :type instance_name: str
        :return: the list of all next processes
        :rtype: List[IProcess]
        """
        next_process_models = self._process_model.get_all_next_processes(instance_name)

        return self._get_process_proxies(next_process_models)

    def get_all_processes(self) -> dict[str, ProcessProxy]:
        """Return all the processes of this protocol

        :return: the list of all processes
        :rtype: List[IProcess]
        """
        process_proxies: dict[str, ProcessProxy] = {}
        for process_instance_name in self._process_model.processes.keys():
            process_proxies[process_instance_name] = self.get_process(process_instance_name)

        return process_proxies

    def _get_process_proxies(self, process_models: set[ProcessModel]) -> set[ProcessProxy]:
        next_processes: set[ProcessProxy] = set()
        for next_process_model in process_models:
            next_processes.add(self.get_process(next_process_model.instance_name))

        return next_processes

    def get_input(self, name):
        return self.get_input_resource_model(name).get_resource()

    def get_input_resource_model(self, name) -> ResourceModel:
        if self.has_parent_protocol():
            return super().get_input_resource_model(name)

        input_task: ProcessProxy = self.get_process(name)
        return input_task.get_output_resource_model(InputTask.output_name)

    def get_output(self, name) -> Resource:
        return self.get_output_resource_model(name).get_resource()

    def get_output_resource_model(self, name) -> ResourceModel:
        if self.has_parent_protocol():
            return super().get_output_resource_model(name)

        output_task: ProcessProxy = self.get_process(name)
        return output_task.get_input_resource_model(OutputTask.input_name)

    ####################################### CONNECTORS #########################################

    def add_connector(self, out_port: ProcessWithPort, in_port: ProcessWithPort) -> None:
        """Add a connector between to process of this protocol

        Exemple :
        protocol.add_connector(create.get_output_port('robot'), sub_proto.get_input_port('robot_i'))
        OR
        protocol.add_connector(create >> 'robot', sub_proto << 'robot_i')
        """
        self.add_connector_by_names(
            out_port.process_instance_name,
            out_port.port_name,
            in_port.process_instance_name,
            in_port.port_name,
        )

    def add_connector_by_names(
        self, from_process_name: str, from_port_name: str, to_process_name: str, to_port_name: str
    ) -> None:
        """Add a connector between to process of this protocol

        Exemple : protocol.add_connector_by_names('create', 'robot', 'sub_proto','robot_i')
        """

        ProtocolService.add_connector_to_protocol(
            self._process_model, from_process_name, from_port_name, to_process_name, to_port_name
        )

    def add_connectors(self, connectors: list[tuple[ProcessWithPort, ProcessWithPort]]) -> None:
        """Add multiple connector inside the protocol

        Exemple : protocol.add_connectors([
            (create >> 'robot', sub_proto << 'robot_i'),
            (sub_proto.get_output_port('robot_o'), robot_travel.get_input_port('robot'))
        ])
        """
        new_connectors: list[ConnectorSpec] = []
        for connector in connectors:
            new_connectors.append(
                {
                    "from_process": connector[0].process_instance_name,
                    "to_process": connector[1].process_instance_name,
                    "from_port": connector[0].port_name,
                    "to_port": connector[1].port_name,
                }
            )

        ProtocolService.add_connectors_to_protocol(self._process_model, new_connectors)

    def delete_connector(self, to_process_name: str, to_port_name: str) -> None:
        """Delete a connector between to process of this protocol

        Exemple : protocol.delete_connector('sub_proto','robot_i')
        """
        ProtocolService.delete_connector_of_protocol(
            self._process_model, to_process_name, to_port_name
        )

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
            self._process_model, name, from_process_name, process_input_name
        )

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
            self._process_model, name, to_process_name, process_ouput_name
        )

    def delete_interface(self, name: str) -> None:
        """Delete an interface of the protocol"""
        ProtocolService.delete_interface_of_protocol(self._process_model, name)

    def delete_outerface(self, name: str) -> None:
        """Delete an outerface of the protocol"""
        ProtocolService.delete_outerface_of_protocol(self._process_model, name)

    ############################################### Port connection checks ####################################

    def is_process_input_port_connected(self, port: ProcessWithPort) -> bool:
        """Check if an input port is connected.
        The method is here because it update the protocol model.

        :param port: The port to check
        :type port: ProcessWithPort
        :return: True if the port is connected, False otherwise
        :rtype: bool
        """
        process = self.get_process(port.process_instance_name)
        port = process.get_input_port(port.port_name)

        return (
            self._process_model.get_connector_from_right(port.process_instance_name, port.port_name)
            is not None
        )

    def is_process_output_port_connected(self, port: ProcessWithPort) -> bool:
        """Check if an output port is connected.
        The method is here because it update the protocol model.

        :param port: The port to check
        :type port: ProcessWithPort
        :return: True if the port is connected, False otherwise
        :rtype: bool
        """
        process = self.get_process(port.process_instance_name)
        port = process.get_output_port(port.port_name)

        return (
            len(
                self._process_model.get_connectors_from_left(
                    port.process_instance_name, port.port_name
                )
            )
            > 0
        )

    def add_process_dynamic_input_port(
        self, process_instance_name: str, port_spec_dto: IOSpecDTO | None = None
    ) -> ProcessWithPort:
        """Add a dynamic input port to the process.
        The method is here because it update the protocol model.

        :param port_name: Name of the port to add
        :type port_name: str
        """
        process = self.get_process(process_instance_name)
        if not process.has_dynamic_inputs():
            raise Exception(f"The process '{process_instance_name}' does not have dynamic inputs")

        update = ProtocolService.add_dynamic_input_port_to_process(
            self.get_model_id(), process_instance_name, port_spec_dto
        )

        self._process_model = update.protocol
        process.refresh()

        input_ports = process.get_input_ports()
        # return the last added port
        return input_ports[-1]

    ############################################### Config ####################################
    # Block config of the protocol because it does not transfer the config to the task

    def set_param(self, param_name: str, value: ParamValue) -> None:
        """Set the param value"""
        raise BadRequestException(
            "The configuration of protocol is not available yet. Please configure the sub task directly"
        )

    def set_config_params(self, config_params: ConfigParamsDict) -> None:
        """Set the config param values"""
        raise BadRequestException(
            "The configuration of protocol is not available yet. Please configure the sub task directly"
        )

    ############################################### Specific processes ####################################

    def add_resource(
        self, instance_name: str | None, resource_model_id: str, in_port: ProcessWithPort = None
    ) -> TaskProxy:
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
        source: ProcessProxy = self.add_process(InputTask, instance_name, config)

        if in_port:
            self.add_connector(source >> InputTask.output_name, in_port)
        return source

    @GwsCoreDbManager.transaction()
    def add_resources_to_process_dynamic_input(
        self, resource_model_ids: list[str], process_instance_name: str
    ) -> list[TaskProxy]:
        """Add multiple resources to a dynamic input port of the protocol and connected them to the in_port.
        It fills the empty dynamic input ports or create new dynamic input ports if needed.
        :param resource_model_ids: the list of resource model ids to add
        :type resource_model_ids: List[str]
        :param in_port: the in port that should receive the resources
        :type in_port: InPort
        :return: the list of created source tasks
        :rtype: List[TaskProxy]
        """

        process = self.get_process(process_instance_name)

        if not process.has_dynamic_inputs():
            raise BadRequestException(
                f"The process '{process_instance_name}' is not using dynamic inputs"
            )

        task_proxies: list[TaskProxy] = []

        for resource_model_id in resource_model_ids:
            # Get all input ports and filter unconnected ones
            all_input_ports: list[ProcessWithPort] = process.get_input_ports()
            free_input_ports: list[ProcessWithPort] = [
                p for p in all_input_ports if not self.is_process_input_port_connected(p)
            ]
            # if there is no more free input port, we need to create a new one
            # otherwise use the free input port
            input_port: ProcessWithPort
            if len(free_input_ports) == 0:
                input_port = self.add_process_dynamic_input_port(process_instance_name)
            else:
                input_port = free_input_ports[0]

            # find the first unconnected port and connect the resource
            task_proxy = self.add_resource(
                instance_name=None,
                resource_model_id=resource_model_id,
                in_port=input_port,
            )
            task_proxies.append(task_proxy)

        # refresh this protocol proxy
        self.refresh()

        return task_proxies

    def add_source(
        self, instance_name: str | None, resource_model_id: str, in_port: ProcessWithPort
    ) -> TaskProxy:
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
        Logger.warning("The add_source method is deprecated, please use add_resource instead")
        return self.add_resource(instance_name, resource_model_id, in_port)

    def add_output(
        self, instance_name: str | None, out_port: ProcessWithPort, flag_resource: bool = True
    ) -> TaskProxy:
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
        output_task = self.add_process(
            OutputTask, instance_name, {OutputTask.flag_config_name: flag_resource}
        )
        self.add_connector(out_port, output_task << OutputTask.input_name)
        return output_task

    def replace_output_with_process(
        self,
        output_instance_name: str,
        instance_name: str,
        process_type: type[Process],
        new_process_input_port_name: str,
        config_params: ConfigParamsDict | None = None,
    ) -> ProcessProxy:
        """Replace an output task by another process (task or protocol).
        Connect the input of the new process to the process that was connected to the output task.

        :param output_instance_name: the instance name of the output task to replace
        :type output_instance_name: str
        :param instance_name: the instance name of the new process
        :type instance_name: str
        :param process_type: the type of the new process (task or protocol)
        :type process_type: Type[Process]
        :param new_process_input_port_name: the name of the input port of the new process
        :type new_process_input_port_name: str
        :param config_params: the config params of the new process, defaults to None
        :type config_params: ConfigParamsDict, optional
        :return: the new process
        :rtype: ProcessProxy
        """
        return self.replace_process(
            existing_process_instance_name=output_instance_name,
            new_process_instance_name=instance_name,
            new_process_process_type=process_type,
            new_process_input_port_name=new_process_input_port_name,
            existing_process_input_port_name=OutputTask.input_name,
            new_process_config_params=config_params,
        )

    def replace_process(
        self,
        existing_process_instance_name: str,
        new_process_instance_name: str,
        new_process_process_type: type[Process],
        new_process_input_port_name: str | None = None,
        existing_process_input_port_name: str | None = None,
        new_process_config_params: ConfigParamsDict | None = None,
    ) -> ProcessProxy:
        """Replace a process (task or protocol) by another process (task or protocol).
        If the new_process_input_port_name and existing_process_input_port_name are provided,
        the input of the new process is connected to the process that was connected
        to the existing_process_input_port_name (replace the process and connect it as the predecessor).

        :param output_instance_name: the instance name of the output task to replace
        :type output_instance_name: str
        :param new_process_instance_name: the instance name of the new process
        :type new_process_instance_name: str
        :param new_process_process_type: the type of the new process (task or protocol)
        :type new_process_process_type: Type[Process]
        :param new_process_input_port_name: the name of the input port of the new process
        :type new_process_input_port_name: str
        :param existing_process_output_port_name: the name of the output port of the existing process
        :type existing_process_output_port_name: str
        :param new_process_config_params: the config params of the new process, defaults to None
        :type new_process_config_params: ConfigParamsDict, optional
        :return: the new process
        :rtype: ProcessProxy
        """
        existing_process = self.get_process(existing_process_instance_name)
        if not existing_process.is_output_task():
            raise BadRequestException(
                f"The process '{existing_process_instance_name}' is not an output task"
            )

        previous_process_name: str | None = None
        previous_process_port_name: str | None = None

        if existing_process_input_port_name and new_process_input_port_name:
            # get the connector to the output task
            connector = self._process_model.get_connector_from_right(
                existing_process.instance_name, existing_process_input_port_name
            )

            if not connector:
                raise BadRequestException(
                    f"The output task '{existing_process.instance_name}' is not connected"
                )

            previous_process_name = connector.left_process.instance_name
            previous_process_port_name = connector.left_port_name

        # delete the output task
        self.delete_process(existing_process.instance_name)

        new_process: ProcessProxy = self.add_process(
            new_process_process_type, new_process_instance_name, new_process_config_params
        )

        if previous_process_name and previous_process_port_name and new_process_input_port_name:
            self.add_connector_by_names(
                previous_process_name,
                previous_process_port_name,
                new_process.instance_name,
                new_process_input_port_name,
            )

        return new_process

        ############################################### CLASS METHODS ####################################

    @classmethod
    def get_by_id(cls, id: str) -> "ProtocolProxy":
        protocol_model: ProtocolModel = ProtocolService.get_by_id_and_check(id)
        return ProtocolProxy(protocol_model)
