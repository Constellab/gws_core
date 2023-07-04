# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Literal, Optional, Set, Type

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.io.io import IO
from gws_core.io.io_spec import InputSpec, IOSpecDict, ResourceType
from gws_core.model.typing_dict import TypingRef
from gws_core.protocol.protocol_dto import ProtocolUpdateDTO
from gws_core.protocol.protocol_layout import (ProcessLayout, ProtocolLayout,
                                               ProtocolLayoutDict)
from gws_core.protocol.protocol_spec import ConnectorSpec
from gws_core.protocol.protocol_types import ProtocolConfigDict
from gws_core.protocol_template.protocol_template import ProtocolTemplate
from gws_core.protocol_template.protocol_template_service import \
    ProtocolTemplateService
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.viewer import Viewer
from gws_core.task.plug import Sink, Source
from gws_core.task.task_input_model import TaskInputModel

from ..config.config_types import ConfigParamsDict
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..io.connector import Connector
from ..io.port import Port
from ..model.typing import Typing
from ..model.typing_manager import TypingManager
from ..process.process import Process
from ..process.process_factory import ProcessFactory
from ..process.process_model import ProcessModel
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
    def create_empty_protocol(cls, instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_empty(
            instance_name=instance_name)

        protocol.save_full()
        return protocol

    ########################## UPDATE PROCESS #####################

    @classmethod
    @transaction()
    def add_process_to_protocol_id(cls, protocol_id: str, process_typing_name: str,
                                   instance_name: str = None) -> ProtocolUpdateDTO:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        process_typing: Typing = TypingManager.get_typing_from_name_and_check(
            process_typing_name)

        return cls.add_process_to_protocol(protocol_model=protocol_model, process_type=process_typing.get_type(),
                                           instance_name=instance_name)

    @classmethod
    @transaction()
    def add_empty_protocol_to_protocol(
            cls, protocol_model: ProtocolModel, instance_name: str = None) -> ProtocolUpdateDTO:
        child_protocol_model: ProtocolModel = ProcessFactory.create_protocol_empty()

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=child_protocol_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_to_protocol(cls, protocol_model: ProtocolModel, process_type: Type[Process],
                                instance_name: str = None, config_params: ConfigParamsDict = None) -> ProtocolUpdateDTO:
        # create the process
        process_model: ProcessModel = ProcessFactory.create_process_model_from_type(
            process_type=process_type, config_params=config_params)

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=process_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_model_to_protocol(cls, protocol_model: ProtocolModel, process_model: ProcessModel,
                                      instance_name: str = None) -> ProtocolUpdateDTO:

        protocol_model.check_is_updatable()
        protocol_model.add_process_model(
            process_model=process_model, instance_name=instance_name)
        # save the new process
        process_model.save_full()

        if process_model.is_source_task():
            process_model.run()

        # Refresh the protocol graph and save
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model, process_model=process_model)

    @classmethod
    @transaction()
    def add_process_connected_to_output(
            cls, protocol_id: str, process_typing_name: str, output_process_name: str, output_port_name: str,
            config_params: ConfigParamsDict = None) -> ProtocolUpdateDTO:
        """Add a process to the protocol and connect it to an output port of a previous process.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(
            output_process_name)

        new_process_type: Type[Process] = TypingManager.get_type_from_name(
            process_typing_name)

        return cls._add_process_connected_to_output(
            protocol_model, new_process_type, existing_process, output_port_name, config_params)

    @classmethod
    @transaction()
    def _add_process_connected_to_output(
            cls, protocol_model: ProtocolModel, new_process_type: Type[Process],
            out_process: ProcessModel, out_port_name: str, config_params: ConfigParamsDict = None) -> ProtocolUpdateDTO:

        input_name: str
        out_port = out_process.out_port(out_port_name)
        # check if any of the new process in port is compatible with the selected out port
        for input_spec_name, input_spec in new_process_type.get_input_specs().get_specs().items():
            if out_port.resource_spec.is_compatible_with_in_spec(input_spec):
                input_name = input_spec_name
                break

        if input_name is None:
            raise BadRequestException(
                "The process has no input port compatible with selected output port")

        # create the process
        protocol_update: ProtocolUpdateDTO = ProtocolService.add_process_to_protocol(
            protocol_model, process_type=new_process_type, config_params=config_params)

        # Create the connector between the provided output port and the new process input port
        protocol_update_2 = cls.add_connector_to_protocol(
            protocol_model, out_process.instance_name, out_port_name,
            protocol_update.process.instance_name, input_name)

        return protocol_update.merge(protocol_update_2)

    @classmethod
    @transaction()
    def add_process_connected_to_input(
            cls, protocol_id: str, process_typing_name: str, input_process_name: str, input_port_name: str,
            config_params: ConfigParamsDict = None) -> ProtocolUpdateDTO:
        """Add a process to the protocol and connect it to an input port of a process.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(
            input_process_name)
        existing_in_port: Port = existing_process.in_port(input_port_name)

        new_process_type: Type[Process] = TypingManager.get_type_from_name(
            process_typing_name)

        output_name: str
        # check if any of the new process out port is compatible with the selected in port
        for output_spec_name, output_spec in new_process_type.get_output_specs().get_specs().items():
            if output_spec.is_compatible_with_in_spec(existing_in_port.resource_spec):
                output_name = output_spec_name
                break

        if output_name is None:
            raise BadRequestException(
                "The process has no output port compatible with selected input port")

        # create the process
        protocol_update: ProtocolUpdateDTO = ProtocolService.add_process_to_protocol(
            protocol_model, process_type=new_process_type, config_params=config_params)

        # Create the connector between the provided input port and the new process output port
        protocol_update_2 = cls.add_connector_to_protocol(
            protocol_model, protocol_update.process.instance_name, output_name,
            existing_process.instance_name, input_port_name)

        return protocol_update.merge(protocol_update_2)

    @classmethod
    def delete_process_of_protocol_id(cls, protocol_id: str, process_instance_name: str) -> ProtocolUpdateDTO:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        return cls.delete_process_of_protocol(
            protocol_model=protocol_model, process_instance_name=process_instance_name)

    @classmethod
    @transaction()
    def delete_process_of_protocol(cls, protocol_model: ProtocolModel, process_instance_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        process_model: ProcessModel = protocol_model.get_process(
            process_instance_name)

        # reset the process before deleting it
        update_protocol = cls.reset_process_of_protocol(
            protocol_model, process_model.instance_name)

        # delete the process from the parent protocol
        protocol_model.remove_process(process_instance_name)
        protocol_model.save_graph()

        # delete the process form the DB
        process_model.delete_instance()

        return update_protocol

    @classmethod
    @transaction()
    def reset_error_process_of_protocol(cls, protocol_model: ProtocolModel) -> ProtocolUpdateDTO:
        error_tasks = protocol_model.get_error_tasks()

        for task in error_tasks:
            cls.reset_process_of_protocol(
                task.parent_protocol, task.instance_name)

    @classmethod
    @transaction()
    def reset_process_of_protocol_id(cls, protocol_id: str, process_instance_name: str) -> ProtocolUpdateDTO:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        return cls.reset_process_of_protocol(protocol_model, process_instance_name)

    @classmethod
    @transaction()
    def reset_process_of_protocol(cls, protocol_model: ProtocolModel, process_instance_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        process_model: ProcessModel = protocol_model.get_process(
            process_instance_name)

        processes_to_reset: Set[ProcessModel] = protocol_model.get_all_next_processes(
            process_instance_name)
        processes_to_reset.add(process_model)

        # Check if any resource generated by the processes are used in another experiment
        process_ids: List[str] = [
            process_model.id for process_model in processes_to_reset]
        process_resources: List[ResourceModel] = list(ResourceModel.get_by_task_models(
            process_ids))
        ResourceModel.check_if_any_resource_is_used_in_another_exp(
            process_resources, protocol_model.experiment.id)

        for process in processes_to_reset:
            process.reset()

        protocol_model.mark_as_partially_run()

        # Delete all the resources previously generated to clear the DB
        ResourceModel.delete_multiple_resources(process_resources)

        # Delete all the TaskInput as well
        # Most of them are deleted when deleting the resource but for some constant inputs (link source)
        # the resource is not deleted but the input must be deleted
        TaskInputModel.delete_by_task_ids(process_ids)

        # re-propagate the resources because some of them might be deleted by the reset
        protocol_model.propagate_resources()

        # refresh the protocol to get the updated graph because the connection and inputs might not be exact
        return ProtocolUpdateDTO(protocol=protocol_model, protocol_updated=True)

    @classmethod
    def _on_protocol_object_updated(cls, protocol_model: ProtocolModel, process_model: ProcessModel = None,
                                    connector: Connector = None, protocol_updated: bool = False) -> ProtocolUpdateDTO:
        """Called when a process or connector is updated.
        """
        protocol_update = ProtocolUpdateDTO(protocol=protocol_model, process=process_model,
                                            connector=connector, protocol_updated=protocol_updated)
        if protocol_model.is_finished:
            protocol_model.mark_as_partially_run()
            protocol_update.protocol_updated = True

        return protocol_update

    ########################## CONNECTORS #####################

    @classmethod
    def add_connectors_to_protocol(
            cls, protocol_model: ProtocolModel, connectors: List[ConnectorSpec]) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        protocol_model.add_connectors(connectors)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model)

    @classmethod
    def add_connector_to_protocol_id(cls, protocol_id: str, from_process_name: str, from_port_name: str,
                                     to_process_name: str, to_port_name: str) -> ProtocolUpdateDTO:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        return cls.add_connector_to_protocol(protocol_model, from_process_name, from_port_name,
                                             to_process_name, to_port_name)

    @classmethod
    def add_connector_to_protocol(
        cls, protocol_model: ProtocolModel, from_process_name: str, from_port_name: str,
            to_process_name: str, to_port_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        connector = protocol_model.add_connector(from_process_name, from_port_name,
                                                 to_process_name, to_port_name)
        protocol_model.save_graph()

        return cls._on_connector_updated(protocol_model, connector, 'create')

    @classmethod
    def delete_connector_of_protocol(
            cls, protocol_id: str, dest_process_name: str, dest_process_port_name: str) -> ProtocolUpdateDTO:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.check_is_updatable()

        connector = protocol_model.delete_connector_from_right(
            dest_process_name, dest_process_port_name)
        protocol_model.save_graph()

        return cls._on_connector_updated(protocol_model, connector, 'delete')

    @classmethod
    def _on_connector_updated(cls, protocol: ProtocolModel, connector: Optional[Connector],
                              mode: Literal['create', 'delete']) -> ProtocolUpdateDTO:
        if connector is None:
            return ProtocolUpdateDTO(protocol=protocol)

        # reset the right process of the connector if it is finished
        if connector.right_process.is_finished:
            update_protocol = cls.reset_process_of_protocol(
                protocol, connector.right_process.instance_name)
            update_protocol.connector = connector
            update_protocol.protocol_updated = True
            return update_protocol

        protocol_updated = False

        if mode == 'create':
            # automatically propagate the resource if the left port has a resource
            if connector.left_port.resource_model:
                connector.propagate_resource()
                # save the right process to save its inputs
                connector.right_process.save()
                protocol_updated = True
        else:
            # in delete mode we always consider the protocol as updated
            # because the next port is resetted
            protocol_updated = True

        return cls._on_protocol_object_updated(
            protocol_model=protocol, connector=connector, protocol_updated=protocol_updated)

    ########################## INTERFACE & OUTERFACE #####################

    @classmethod
    def add_interface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str, target_process_name: str, target_port_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        protocol_model.add_interface(
            name, target_process_name, target_port_name)
        protocol_model.save_graph()
        return cls._on_protocol_object_updated(protocol_model=protocol_model)

    @classmethod
    def add_outerface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str, source_process_name: str, source_port_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        protocol_model.add_outerface(
            name, source_process_name, source_port_name)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model)

    @classmethod
    def delete_interface_of_protocol_id(cls, protocol_id: str, interface_name: str) -> ProtocolUpdateDTO:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        return cls.delete_interface_of_protocol(protocol_model, interface_name)

    @classmethod
    def delete_interface_of_protocol(cls, protocol_model: ProtocolModel, interface_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        protocol_model.remove_interface(interface_name)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model)

    @classmethod
    def delete_outerface_of_protocol_id(cls, protocol_id: str, outerface_name: str) -> ProtocolUpdateDTO:
        protocol_model = cls.get_protocol_by_id(protocol_id)
        return cls.delete_outerface_of_protocol(protocol_model, outerface_name)

    @classmethod
    def delete_outerface_of_protocol(cls, protocol_model: ProtocolModel, outerface_name: str) -> ProtocolUpdateDTO:
        protocol_model.check_is_updatable()
        protocol_model.remove_outerface(outerface_name)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model)

    @classmethod
    @transaction()
    def copy_protocol(cls, protocol_model: ProtocolModel) -> ProtocolModel:
        new_protocol_model: ProtocolModel = ProcessFactory.copy_protocol(
            protocol_model)
        new_protocol_model.save_full()
        new_protocol_model.reset()
        return new_protocol_model

    ########################## CONFIG #####################

    @classmethod
    @transaction()
    def configure_process(
            cls, protocol_id: str, process_instance_name: str, config_values: ConfigParamsDict) -> ProtocolUpdateDTO:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.check_is_updatable()
        process_model: ProcessModel = protocol_model.get_process(
            process_instance_name)

        update_dto: ProtocolUpdateDTO = ProtocolUpdateDTO(
            protocol=protocol_model, process=process_model)

        # reset the process and next processes if required
        if process_model.is_finished:
            cls.reset_process_of_protocol(
                protocol_model, process_model.instance_name)
            update_dto.protocol_updated = True
        elif protocol_model.is_finished:
            protocol_model.mark_as_partially_run()
            update_dto.protocol_updated = True

        # set config value and save
        process_model.config.set_values(config_values)
        process_model.config.save()

        # For task of type Source, we store the resource id in task table
        if isinstance(process_model, TaskModel) and process_model.is_source_task():
            resource_model_id = Source.get_resource_id_from_config(
                config_values)

            if resource_model_id is not None:
                process_model.source_config_id = ResourceModel.get_by_id_and_check(
                    resource_model_id).id
            else:
                process_model.source_config_id = None
            process_model.save()

        return update_dto

    ########################## SPECIFIC PROCESS #####################
    @classmethod
    def add_source_to_protocol_id(
            cls, protocol_id: str, resource_id: str) -> ProtocolUpdateDTO:
        """ Add a source task to the protocol. Configure it with the resource.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        # Create source task model
        source: TaskModel = ProcessFactory.create_source(resource_id)

        # Add the source to the protocol
        return cls.add_process_model_to_protocol(
            protocol_model, source)

    @classmethod
    def add_source_to_process_input(
            cls, protocol_id: str, resource_id: str, process_name: str, input_port_name: str) -> ProtocolUpdateDTO:
        """ Add a source task to the protocol. Configure it with the resource. And add connector
            from source to process
        """
        return cls.add_process_connected_to_input(
            protocol_id, Source._typing_name, process_name, input_port_name, {Source.config_name: resource_id})

    @classmethod
    def add_sink_to_process_ouput(
            cls, protocol_id: str, process_name: str, output_port_name: str) -> ProtocolUpdateDTO:
        """ Add a sink task to the protocol. And add connector from process to sink
        """

        return cls.add_process_connected_to_output(protocol_id, Sink._typing_name, process_name, output_port_name)

    @classmethod
    @transaction()
    def add_viewer_to_process_output(
            cls, protocol_id: str, process_name: str, output_port_name: str) -> ProtocolUpdateDTO:
        """ Add a view task to the protocol. And add connector from process to view task
        """

        # retrieve the type of the output process port to pre-configure the Viewer
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(
            process_name)
        existing_out_port: Port = existing_process.out_port(output_port_name)

        viewer_config = {
            Viewer.resource_config_name: existing_out_port.get_default_resource_type()._typing_name}

        return cls.add_process_connected_to_output(
            protocol_id, Viewer._typing_name, process_name, output_port_name,
            viewer_config)

    ########################## LAYOUT #####################

    @classmethod
    def save_layout(cls, protocol_id: str, layout_dict: ProtocolLayoutDict) -> None:
        layout = ProtocolLayout(layout_dict)
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout = layout
        protocol_model.save()

    @classmethod
    def save_process_layout(cls, protocol_id: str, process_instance_name: str, layout: ProcessLayout) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout.set_process(process_instance_name, layout)
        protocol_model.save()

    @classmethod
    def save_interface_layout(cls, protocol_id: str, interface_name: str, layout: ProcessLayout) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout.set_interface(interface_name, layout)
        protocol_model.save()

    @classmethod
    def save_outerface_layout(cls, protocol_id: str, outerface_name: str, layout: ProcessLayout) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout.set_outerface(outerface_name, layout)
        protocol_model.save()

    ########################## DYNAMIC PORTS #####################

    @classmethod
    def add_dynamic_input_port_to_process(
            cls, protocol_id: str, process_name: str) -> ProtocolUpdateDTO:
        return cls._add_dynamic_port_to_process(protocol_id, process_name, 'input')

    @classmethod
    def add_dynamic_output_port_to_process(
            cls, protocol_id: str, process_name: str) -> ProtocolUpdateDTO:
        return cls._add_dynamic_port_to_process(protocol_id, process_name, 'output')

    @classmethod
    def _add_dynamic_port_to_process(cls, protocol_id: str, process_name: str,
                                     port_type: Literal['input', 'output']) -> ProtocolUpdateDTO:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        # reset the process
        update_protocol = cls.reset_process_of_protocol(protocol_model, process_name)

        process_model: ProcessModel = protocol_model.get_process(process_name)
        io: IO = process_model.inputs if port_type == 'input' else process_model.outputs
        if not io.is_dynamic:
            raise BadRequestException(f"The process does not support dynamic {port_type} ports")

        io.create_port(StringHelper.generate_uuid(), InputSpec(resource_types=[Resource]))
        process_model.save()
        new_update = ProtocolUpdateDTO(protocol=protocol_model, protocol_updated=False,
                                       process=process_model)
        return update_protocol.merge(new_update)

    @classmethod
    def delete_dynamic_input_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str) -> ProtocolUpdateDTO:
        return cls._delete_dynamic_port_of_process(protocol_id, process_name, port_name, 'input')

    @classmethod
    def delete_dynamic_output_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str) -> ProtocolUpdateDTO:
        return cls._delete_dynamic_port_of_process(protocol_id, process_name, port_name, 'output')

    @classmethod
    @transaction()
    def _delete_dynamic_port_of_process(cls, protocol_id: str, process_name: str,
                                        port_name: str, port_type: Literal['input', 'output']) -> ProtocolUpdateDTO:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        # reset the process
        update_protocol = cls.reset_process_of_protocol(protocol_model, process_name)

        process_model: ProcessModel = protocol_model.get_process(process_name)

        io: IO = process_model.inputs if port_type == 'input' else process_model.outputs

        if not io.is_dynamic:
            raise BadRequestException(f"The process does not support dynamic {port_type} ports")

        if port_type == 'input':
            protocol_model.delete_connector_from_right(process_name, port_name)
        else:
            protocol_model.delete_connectors_from_left(process_name, port_name)
        protocol_model.save_graph()

        io.remove_port(port_name)
        process_model.save()
        new_update = ProtocolUpdateDTO(protocol=protocol_model, protocol_updated=True,
                                       process=process_model)
        return update_protocol.merge(new_update)

    ########################## PROTOCOL TEMPLATE #####################

    @classmethod
    def create_protocol_template_from_id(
            cls, protocol_id: str, name: str, description: dict = None) -> ProtocolTemplate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)
        return ProtocolTemplateService.create_from_protocol(protocol=protocol_model,
                                                            name=name, description=description)

    @classmethod
    def create_protocol_model_from_template(cls, protocol_template: ProtocolTemplate) -> ProtocolModel:
        try:
            return cls.create_protocol_model_from_graph(protocol_template.get_template())
        except Exception as e:
            raise BadRequestException(
                f"The template is not compatible with the current version. {e}")

    @classmethod
    def create_protocol_model_from_graph(cls, graph: ProtocolConfigDict) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_graph(
            graph=graph)

        protocol.save_full()
        return protocol

    @classmethod
    def generate_protocol_template(cls, protocol_id: str) -> ProtocolTemplate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        if not protocol_model.experiment:
            raise BadRequestException("Cannot download a protocol without experiment")

        return ProtocolTemplate.from_protocol_model(protocol_model,
                                                    protocol_model.experiment.title,
                                                    protocol_model.experiment.description)
