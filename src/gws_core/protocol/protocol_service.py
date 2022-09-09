# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Tuple, Type

from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.viewer import Viewer
from gws_core.task.plug import Sink, Source

from ..config.config_types import ConfigParamsDict
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..io.connector import Connector
from ..io.port import InPort, OutPort, Port
from ..model.typing import Typing
from ..model.typing_manager import TypingManager
from ..process.process import Process
from ..process.process_factory import ProcessFactory
from ..process.process_model import ProcessModel
from ..process.protocol_sub_process_builder import SubProcessBuilderUpdate
from ..protocol.protocol_action import AddProcessWithLink
from ..protocol.protocol_model import ProtocolModel
from ..task.task_model import TaskModel
from .protocol import Protocol


class ProtocolService(BaseService):

    ########################## GET #####################

    @classmethod
    def get_protocol_by_id(cls, id: str) -> ProtocolModel:
        return ProtocolModel.get_by_id_and_check(id)

    ########################## CREATE #####################
    @classmethod
    def create_protocol_model_from_type(cls, protocol_type: Type[Protocol], instance_name: str = None,
                                        config_params: ConfigParamsDict = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=protocol_type, instance_name=instance_name, config_params=config_params)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_model_from_data(cls, processes: dict = None,
                                        connectors: list = None,
                                        interfaces: dict = None,
                                        outerfaces: dict = None,
                                        instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_data(
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
            instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_empty_protocol(cls, instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_empty(instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_model_from_graph(cls, graph: dict) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_graph(
            graph=graph)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_model_from_task_model(cls, task_model: TaskModel) -> ProtocolModel:
        if not isinstance(task_model, TaskModel):
            raise BadRequestException("A ProcessModel is required")
        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_data(
            processes={task_model.instance_name: task_model}, connectors=[], interfaces={}, outerfaces={})

        protocol.save_full()
        return protocol

    ########################## UPDATE PROCESS #####################
    @classmethod
    def update_protocol_graph(cls, protocol_model: ProtocolModel, graph: dict) -> ProtocolModel:
        protocol_model.check_is_updatable()
        new_protocol: ProtocolModel = cls._update_protocol_graph_recur(
            protocol_model, graph)

        new_protocol.save_full()
        return new_protocol

    @classmethod
    def _update_protocol_graph_recur(cls, protocol_model: ProtocolModel, graph: dict) -> ProtocolModel:

        for process in protocol_model.processes.values():
            # disconnect the port to prevent connection errors later
            process.disconnect()

        cls._remove_orphan_process(protocol_model=protocol_model, nodes=graph["nodes"])

        protocol_model.build_from_graph(
            graph=graph, sub_process_factory=SubProcessBuilderUpdate())

        for key, process in protocol_model.processes.items():

            # If this is a sub protocol and it's graph is defined
            if isinstance(process, ProtocolModel) and 'graph' in graph["nodes"][key]['data']:
                cls._update_protocol_graph_recur(
                    protocol_model=process, graph=graph["nodes"][key]["data"]["graph"])

        # Init the connector afterward because its needs the child to init correctly
        protocol_model.disconnect_connectors()
        protocol_model.init_connectors_from_graph(graph["links"])

        return protocol_model

    @classmethod
    def _remove_orphan_process(cls, protocol_model: ProtocolModel, nodes: dict) -> None:
        """Method to remove the removed process when saving a new protocols

        :param nodes: [description]
        :type nodes: Dict
        """
        process_names = []
        for name, process in protocol_model.processes.items():
            # if the process is not in the Dict or its type has changed, remove it
            if not name in nodes or process.process_typing_name != nodes[name].get("process_typing_name"):
                process_names.append(name)

        for name in process_names:
            cls.delete_process_of_protocol(protocol_model, name)

    @classmethod
    @transaction()
    def add_process_to_protocol_id(cls, protocol_id: str, process_typing_name: str,
                                   instance_name: str = None) -> ProcessModel:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_typing: Typing = TypingManager.get_typing_from_name_and_check(process_typing_name)

        return cls.add_process_to_protocol(protocol_model=protocol_model, process_type=process_typing.get_type(),
                                           instance_name=instance_name)

    @classmethod
    @transaction()
    def add_empty_protocol_to_protocol(cls, protocol_model: ProtocolModel, instance_name: str = None) -> ProcessModel:
        child_protocol_model: ProtocolModel = ProcessFactory.create_protocol_empty()

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=child_protocol_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_to_protocol(cls, protocol_model: ProtocolModel, process_type: Type[Process],
                                instance_name: str = None, config_params: ConfigParamsDict = None) -> ProcessModel:
        # create the process
        process_model: ProcessModel = ProcessFactory.create_process_model_from_type(
            process_type=process_type, config_params=config_params)

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=process_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_model_to_protocol(cls, protocol_model: ProtocolModel, process_model: ProcessModel,
                                      instance_name: str = None) -> ProcessModel:

        protocol_model.check_is_updatable()
        protocol_model.add_process_model(process_model=process_model, instance_name=instance_name)
        # save the new process
        process_model.save_full()

        # Refresh the protocol graph and save
        protocol_model.save(update_graph=True)

        return process_model

    @classmethod
    @transaction()
    def add_process_connected_to_output(
            cls, protocol_id: str, process_typing_name: str, output_process_name: str, output_port_name: str,
            config_params: ConfigParamsDict = None) -> AddProcessWithLink:
        """Add a process to the protocol and connect it to an output port of a previous process.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(output_process_name)
        existing_out_port: Port = existing_process.out_port(output_port_name)

        new_process_type: Type[Process] = TypingManager.get_type_from_name(process_typing_name)

        return cls._add_process_connected_to_output(protocol_model, new_process_type, existing_out_port, config_params)

    @classmethod
    @transaction()
    def _add_process_connected_to_output(
            cls, protocol_model: ProtocolModel, new_process_type: Type[Process],
            existing_out_port: Port, config_params: ConfigParamsDict = None) -> AddProcessWithLink:

        input_name: str
        # check if any of the new process in port is compatible with the selected out port
        for input_spec_name, input_spec in new_process_type.get_input_specs().items():
            if existing_out_port.resource_spec.is_compatible_with_in_spec(input_spec):
                input_name = input_spec_name
                break

        if input_name is None:
            raise BadRequestException("The process has no input port compatible with selected output port")

        # create the process
        new_process: ProcessModel = ProtocolService.add_process_to_protocol(
            protocol_model, process_type=new_process_type, config_params=config_params)

        # Create the connector between the provided output port and the new process input port
        connector = cls.add_connector_to_protocol(protocol_model, existing_out_port,
                                                  new_process.in_port(input_name))

        return AddProcessWithLink(process_model=new_process, connector=connector)

    @classmethod
    @transaction()
    def add_process_connected_to_input(
            cls, protocol_id: str, process_typing_name: str, input_process_name: str, input_port_name: str,
            config_params: ConfigParamsDict = None) -> AddProcessWithLink:
        """Add a process to the protocol and connect it to an input port of a process.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(input_process_name)
        existing_in_port: Port = existing_process.in_port(input_port_name)

        new_process_type: Type[Process] = TypingManager.get_type_from_name(process_typing_name)

        output_name: str
        # check if any of the new process out port is compatible with the selected in port
        for output_spec_name, output_spec in new_process_type.get_output_specs().items():
            if output_spec.is_compatible_with_in_spec(existing_in_port.resource_spec):
                output_name = output_spec_name
                break

        if output_name is None:
            raise BadRequestException("The process has no output port compatible with selected input port")

        # create the process
        new_process: ProcessModel = ProtocolService.add_process_to_protocol(
            protocol_model, process_type=new_process_type, config_params=config_params)

        # Create the connector between the provided input port and the new process output port
        connector = cls.add_connector_to_protocol(protocol_model, new_process.out_port(output_name),
                                                  existing_in_port)

        return AddProcessWithLink(process_model=new_process, connector=connector)

    @classmethod
    def delete_process_of_protocol_id(cls, protocol_id: str, process_instance_name: str) -> None:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        cls.delete_process_of_protocol(protocol_model=protocol_model, process_instance_name=process_instance_name)

    @classmethod
    @transaction()
    def delete_process_of_protocol(cls, protocol_model: ProtocolModel, process_instance_name: str) -> None:
        protocol_model.check_is_updatable()
        process_model: ProcessModel = protocol_model.get_process(process_instance_name)

        # delete the process from the parent protocol
        protocol_model.remove_process(process_instance_name)
        protocol_model.save(update_graph=True)

        # delete the process form the DB
        process_model.delete_instance()

    ########################## CONNECTORS #####################

    @classmethod
    def add_connectors_to_protocol(
            cls, protocol_model: ProtocolModel, connectors: List[Tuple[OutPort, InPort]]) -> ProtocolModel:
        protocol_model.check_is_updatable()
        for connector in connectors:
            new_connector: Connector = Connector(connector[0], connector[1])
            protocol_model.add_connector(new_connector)
        return protocol_model.save(update_graph=True)

    @classmethod
    def add_connector_to_protocol_id(cls, protocol_id: str, output_process_name: str, out_port_name: str,
                                     input_process_name: str, in_port_name: str) -> Connector:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        output_process: ProcessModel = protocol_model.get_process(output_process_name)
        input_process: ProcessModel = protocol_model.get_process(input_process_name)

        return cls.add_connector_to_protocol(protocol_model, output_process.out_port(out_port_name),
                                             input_process.in_port(in_port_name))

    @classmethod
    def add_connector_to_protocol(
            cls, protocol_model: ProtocolModel, out_port: OutPort, in_port: InPort) -> Connector:
        protocol_model.check_is_updatable()
        connector: Connector = Connector(out_port, in_port)
        protocol_model.add_connector(connector)
        protocol_model.save(update_graph=True)
        return connector

    @classmethod
    def delete_connector_of_protocol(
            cls, protocol_id: str, dest_process_name: str, dest_process_port_name: str) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        protocol_model.check_is_updatable()
        protocol_model.delete_connector_from_right(dest_process_name, dest_process_port_name)
        protocol_model.save(update_graph=True)

    ########################## INTERFACE & OUTERFACE #####################
    @classmethod
    def add_interface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str, in_port: InPort) -> ProtocolModel:
        protocol_model.check_is_updatable()
        protocol_model.add_interface(name, in_port)
        return protocol_model.save(update_graph=True)

    @classmethod
    def add_outerface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str, out_port: OutPort) -> ProtocolModel:
        protocol_model.check_is_updatable()
        protocol_model.add_outerface(name, out_port)
        return protocol_model.save(update_graph=True)

    @classmethod
    def delete_interface_of_protocol_id(cls, protocol_id: str, interface_name: str) -> None:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        cls.delete_interface_of_protocol(protocol_model, interface_name)

    @classmethod
    def delete_interface_of_protocol(cls, protocol_model: ProtocolModel, interface_name: str) -> None:
        protocol_model.check_is_updatable()
        protocol_model.remove_interface(interface_name)
        protocol_model.save(update_graph=True)

    @classmethod
    def delete_outerface_of_protocol_id(cls, protocol_id: str, outerface_name: str) -> None:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        cls.delete_outerface_of_protocol(protocol_model, outerface_name)

    @classmethod
    def delete_outerface_of_protocol(cls, protocol_model: ProtocolModel, outerface_name: str) -> None:
        protocol_model.check_is_updatable()
        protocol_model.remove_outerface(outerface_name)
        protocol_model.save(update_graph=True)

    @classmethod
    @transaction()
    def copy_protocol(cls, protocol_model: ProtocolModel) -> ProtocolModel:
        new_protocol_model: ProtocolModel = ProcessFactory.copy_protocol(protocol_model)
        new_protocol_model.save_full()
        new_protocol_model.reset()
        return new_protocol_model

    ########################## CONFIG #####################

    @classmethod
    @transaction()
    def configure_process(cls, protocol_id: str, process_instance_name: str, config_values: ConfigParamsDict) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        protocol_model.check_is_updatable()
        process_model: ProcessModel = protocol_model.get_process(process_instance_name)

        # set config value and save
        process_model.config.set_values(config_values)
        process_model.config.save()

        # For task of type Source, we store the resource id in task table
        if isinstance(process_model, TaskModel) and process_model.is_source_task():
            resource_model_id = Source.get_resource_id_from_config(config_values)

            if resource_model_id is not None:
                process_model.source_config_id = ResourceModel.get_by_id_and_check(resource_model_id).id
            else:
                process_model.source_config_id = None
            process_model.save()

    ########################## SPECIFIC PROCESS #####################
    @classmethod
    def add_source_to_protocol_id(
            cls, protocol_id: str, resource_id: str) -> ProcessModel:
        """ Add a source task to the protocol. Configure it with the resource.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        # Create source task model
        source: TaskModel = ProcessFactory.create_source(resource_id)

        # Add the source to the protocol
        source_model: ProcessModel = cls.add_process_model_to_protocol(protocol_model, source)

        return source_model

    @classmethod
    def add_source_to_process_input(
            cls, protocol_id: str, resource_id: str, process_name: str, input_port_name: str, ) -> AddProcessWithLink:
        """ Add a source task to the protocol. Configure it with the resource. And add connector
            from source to process
        """
        return cls.add_process_connected_to_input(protocol_id, Source._typing_name, process_name, input_port_name,
                                                  {Source.config_name: resource_id})

    @classmethod
    def add_sink_to_process_ouput(
            cls, protocol_id: str, process_name: str, output_port_name: str) -> AddProcessWithLink:
        """ Add a sink task to the protocol. And add connector from process to sink
        """

        return cls.add_process_connected_to_output(protocol_id, Sink._typing_name, process_name, output_port_name)

    @classmethod
    @transaction()
    def add_viewer_to_process_output(
            cls, protocol_id: str, process_name: str, output_port_name: str) -> AddProcessWithLink:
        """ Add a view task to the protocol. And add connector from process to view task
        """

        # retrieve the type of the output process port to pre-configure the Viewer
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(process_name)
        existing_out_port: Port = existing_process.out_port(output_port_name)

        viewer_config = {Viewer.resource_config_name: existing_out_port.get_default_resource_type()._typing_name}

        return cls.add_process_connected_to_output(
            protocol_id, Viewer._typing_name, process_name, output_port_name,
            viewer_config)
