

from typing import Any, Dict, List, Literal, Optional, Set, Type, Union

from gws_core.config.config_dto import ConfigSimpleDTO
from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.config.param.param_types import (DynamicParamAllowedSpecsDict,
                                               ParamSpecDTO, ParamValue)
from gws_core.core.utils.string_helper import StringHelper
from gws_core.entity_navigator.entity_navigator import EntityNavigatorResource
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.impl.live.base.env_agent import EnvAgent
from gws_core.impl.live.py_agent import PyAgent
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io import IO
from gws_core.io.io_spec import InputSpec, IOSpec, IOSpecDTO, OutputSpec
from gws_core.io.ioface import IOface
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_dto import ProcessDTO
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.protocol.protocol_graph_factory import \
    ProtocolGraphFactoryFromType
from gws_core.protocol.protocol_layout import (ProcessLayoutDTO,
                                               ProtocolLayout,
                                               ProtocolLayoutDTO)
from gws_core.protocol.protocol_spec import ConnectorSpec
from gws_core.protocol.protocol_update import ProtocolUpdate
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.viewer import Viewer
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.scenario_template.scenario_template_factory import \
    ScenarioTemplateFactory
from gws_core.scenario_template.scenario_template_service import \
    ScenarioTemplateService
from gws_core.streamlit.streamlit_agent import StreamlitAgent
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask
from gws_core.user.current_user_service import CurrentUserService

from ..code.agent_factory import AgentFactory
from ..community.community_dto import (CommunityAgentDTO,
                                       CommunityAgentFileDTO,
                                       CommunityAgentVersionCreateResDTO,
                                       CommunityAgentVersionDTO,
                                       CommunityCreateAgentDTO)
from ..community.community_service import CommunityService
from ..config.config_types import ConfigParamsDict
from ..config.param.param_types import ParamSpecVisibilty
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
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


class ProtocolService():

    ########################## GET #####################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> ProtocolModel:
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
                                   instance_name: str = None, config_params: ConfigParamsDict = None) -> ProtocolUpdate:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        process_typing: Typing = TypingManager.get_typing_from_name_and_check(
            process_typing_name)

        return cls.add_process_to_protocol(protocol_model=protocol_model, process_type=process_typing.get_type(),
                                           instance_name=instance_name, config_params=config_params)

    @classmethod
    @transaction()
    def duplicate_process_to_protocol_id(cls, protocol_id: str, process_instance_name: str) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        if protocol_model is None:
            raise BadRequestException("The protocol does not exist")

        process_model: TaskModel = protocol_model.get_process(process_instance_name)

        if process_model is None:
            raise BadRequestException("The process does not exist in the protocol")

        duplicate_process_model: ProcessModel = None
        if isinstance(process_model, TaskModel):
            duplicate_process_model = ProcessFactory.create_task_model_from_type(
                task_type=process_model.get_process_type(),
                config_params=process_model.config.get_values(),
                inputs_dto=process_model.to_config_dto().inputs,
                outputs_dto=process_model.to_config_dto().outputs,
                style=process_model.style,
                community_agent_version_id=process_model.community_agent_version_id,
                name=process_model.name + " (copy)"
            )
        elif isinstance(process_model, ProtocolModel):
            factory = ProtocolGraphFactoryFromType(process_model.to_protocol_config_dto())
            duplicate_process_model = factory.create_protocol_model()

        if duplicate_process_model is None:
            raise BadRequestException("The process does not exist in the protocol")

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=duplicate_process_model)

    @classmethod
    @transaction()
    def add_empty_protocol_to_protocol_id(cls, protocol_id: str) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        return cls.add_empty_protocol_to_protocol(protocol_model=protocol_model, name="Sub-scenario")

    @classmethod
    @transaction()
    def add_empty_protocol_to_protocol(
            cls, protocol_model: ProtocolModel, instance_name: str = None,
            name: str = None) -> ProtocolUpdate:
        child_protocol_model: ProtocolModel = ProcessFactory.create_protocol_empty(
            name=name, instance_name=instance_name)

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=child_protocol_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_to_protocol(cls, protocol_model: ProtocolModel, process_type: Type[Process],
                                instance_name: str = None, config_params: ConfigParamsDict = None) -> ProtocolUpdate:
        # create the process
        process_model: ProcessModel = ProcessFactory.create_process_model_from_type(
            process_type=process_type, config_params=config_params)

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=process_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_model_to_protocol(cls, protocol_model: ProtocolModel, process_model: ProcessModel,
                                      instance_name: str = None) -> ProtocolUpdate:

        protocol_model.check_is_updatable(error_if_finished=False)
        protocol_model.add_process_model(
            process_model=process_model, instance_name=instance_name)
        # save the new process
        process_model.save_full()

        # run the next process if it is auto run
        protocol_model.run_auto_run_processes()

        # Refresh the protocol graph and save
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model, process_model=process_model)

    @classmethod
    @transaction()
    def add_process_connected_to_output(
            cls, protocol_id: str, process_typing_name: str, output_process_name: str, output_port_name: str,
            config_params: ConfigParamsDict = None) -> ProtocolUpdate:
        """Add a process to the protocol and connect it to an output port of a previous process.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(
            output_process_name)

        new_process_type: Type[Process] = TypingManager.get_and_check_type_from_name(
            process_typing_name)

        return cls._add_process_connected_to_output(
            protocol_model, new_process_type, existing_process, output_port_name, config_params)

    @classmethod
    @transaction()
    def _add_process_connected_to_output(
            cls, protocol_model: ProtocolModel, new_process_type: Type[Process],
            out_process: ProcessModel, out_port_name: str, config_params: ConfigParamsDict = None) -> ProtocolUpdate:

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
        protocol_update: ProtocolUpdate = ProtocolService.add_process_to_protocol(
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
            config_params: ConfigParamsDict = None) -> ProtocolUpdate:
        """Add a process to the protocol and connect it to an input port of a process.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(
            input_process_name)
        existing_in_port: Port = existing_process.in_port(input_port_name)

        new_process_type: Type[Process] = TypingManager.get_and_check_type_from_name(
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
        protocol_update: ProtocolUpdate = ProtocolService.add_process_to_protocol(
            protocol_model, process_type=new_process_type, config_params=config_params)

        # Create the connector between the provided input port and the new process output port
        protocol_update_2 = cls.add_connector_to_protocol(
            protocol_model, protocol_update.process.instance_name, output_name,
            existing_process.instance_name, input_port_name)

        return protocol_update.merge(protocol_update_2)

    @classmethod
    def delete_process_of_protocol_id(cls, protocol_id: str, process_instance_name: str) -> ProtocolUpdate:
        protocol_model = cls.get_by_id_and_check(protocol_id)
        return cls.delete_process_of_protocol(
            protocol_model=protocol_model, process_instance_name=process_instance_name)

    @classmethod
    @transaction()
    def delete_process_of_protocol(cls, protocol_model: ProtocolModel, process_instance_name: str) -> ProtocolUpdate:
        process_model: ProcessModel = protocol_model.get_process(process_instance_name)
        process_model.check_is_updatable()

        # delete the process from the parent protocol
        protocol_model.remove_process(process_instance_name)
        protocol_model.save_graph()

        # update the protocol model status
        protocol_model.refresh_status()

        # delete the process form the DB
        process_model.delete_instance()

        return ProtocolUpdate(protocol=protocol_model, protocol_updated=True, process=process_model)

    @classmethod
    @transaction()
    def reset_process_of_protocol(cls, protocol_model: ProtocolModel, process_instance_name: str) -> ProtocolUpdate:
        process_model: ProcessModel = protocol_model.get_process(process_instance_name)
        process_model.check_is_updatable(error_if_finished=False)

        processes_to_reset: Set[ProcessModel] = protocol_model.get_all_next_processes(
            process_instance_name)
        processes_to_reset.add(process_model)
        for process in processes_to_reset:
            process.reset()

        # re-propagate the resources because some of them might be deleted by the reset
        protocol_model.propagate_resources()
        protocol_model.refresh_status()

        # add all the sub protocols that were resetted
        sub_resetted_protocols: Set[ProtocolModel] = {
            protocol_model for protocol_model in processes_to_reset if isinstance(protocol_model, ProtocolModel)}

        # refresh the protocol to get the updated graph because the connection and inputs might not be exact
        return ProtocolUpdate(protocol=protocol_model, protocol_updated=True, sub_protocols=sub_resetted_protocols)

    @classmethod
    def run_process(cls, protocol_id: str, process_instance_name: str) -> ProtocolUpdate:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        # ScenarioRunService.run_scenario_process(protocol_model.scenario, protocol_model, process_instance_name)
        ScenarioRunService.create_cli_for_scenario_process(
            protocol_model.scenario, protocol_model, process_instance_name,
            CurrentUserService.get_and_check_current_user())

        # if the process is fast, this is useful to return the finished process
        # sleep(4)
        return ProtocolUpdate(protocol=protocol_model.refresh(), protocol_updated=True)

    @classmethod
    def _on_protocol_object_updated(cls, protocol_model: ProtocolModel, process_model: ProcessModel = None,
                                    connector: Connector = None, ioface: IOface = None,
                                    protocol_updated: bool = False) -> ProtocolUpdate:
        """Called when a process or connector is updated.
        """
        protocol_update = ProtocolUpdate(protocol=protocol_model, process=process_model,
                                         connector=connector, ioface=ioface,
                                         protocol_updated=protocol_updated)

        # refresh the protocol status for auto run processes, or run partially
        current_status = protocol_model.status
        protocol_model.refresh_status()
        if current_status != protocol_model.status:
            protocol_update.protocol_updated = True

        return protocol_update

    @classmethod
    def _get_process_of_protocol(cls, protocol_model_id: str, process_instance_name: str) -> ProcessModel:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_model_id)
        return protocol_model.get_process(process_instance_name)

    ########################## CONNECTORS #####################
    @classmethod
    def add_connector_to_protocol_id(cls, protocol_id: str, from_process_name: str, from_port_name: str,
                                     to_process_name: str, to_port_name: str) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        return cls.add_connector_to_protocol(protocol_model, from_process_name, from_port_name,
                                             to_process_name, to_port_name)

    @classmethod
    def add_connectors_to_protocol(
            cls, protocol_model: ProtocolModel, connectors: List[ConnectorSpec]) -> ProtocolUpdate:
        protocol_model.check_is_updatable()
        protocol_model.add_connectors(connectors)
        protocol_model.save_graph()

        # run the next process if it is auto run
        protocol_model.run_auto_run_processes()

        return cls._on_protocol_object_updated(protocol_model)

    @classmethod
    def add_connector_to_protocol(
        cls, protocol_model: ProtocolModel, from_process_name: str, from_port_name: str,
            to_process_name: str, to_port_name: str) -> ProtocolUpdate:
        protocol_model.check_is_updatable()
        connector = protocol_model.add_connector(from_process_name, from_port_name,
                                                 to_process_name, to_port_name)

        # run the next process if it is auto run
        protocol_model.run_auto_run_processes()
        protocol_model.save_graph()

        return cls._on_connector_updated(protocol_model, connector)

    @classmethod
    @transaction()
    def delete_connector_of_protocol(
            cls, protocol_id: str, dest_process_name: str, dest_process_port_name: str) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.check_is_updatable()

        connector = protocol_model.delete_connector_from_right(dest_process_name, dest_process_port_name)
        protocol_model.save_graph()

        return cls._on_connector_updated(protocol_model, connector)

    @classmethod
    def _on_connector_updated(cls, protocol: ProtocolModel, connector: Optional[Connector]) -> ProtocolUpdate:
        if connector is None:
            return ProtocolUpdate(protocol=protocol)

        # reset the right process of the connector if it is finished
        connector.right_process.check_is_updatable()

        # save the right process to save its inputs (new or deleted)
        connector.right_process.save()

        return cls._on_protocol_object_updated(
            protocol_model=protocol, connector=connector, protocol_updated=True)

    ########################## INTERFACE & OUTERFACE #####################

    @classmethod
    def add_interface_to_protocol_id(
            cls, protocol_model_id: str,
            target_process_name: str, target_port_name: str) -> ProtocolUpdate:
        protocol_model = cls.get_by_id_and_check(protocol_model_id)
        return cls.add_interface_to_protocol(
            protocol_model, protocol_model.generate_interface_name(),
            target_process_name, target_port_name)

    @classmethod
    def add_interface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str,
            target_process_name: str, target_port_name: str) -> ProtocolUpdate:
        protocol_model.check_is_updatable()

        if protocol_model.is_root_process():
            raise BadRequestException(
                "Cannot add an interface to the root protocol")
        ioface = protocol_model.add_interface(
            name, target_process_name, target_port_name)
        protocol_model.save_graph()
        return cls._on_protocol_object_updated(protocol_model=protocol_model,
                                               ioface=ioface,
                                               protocol_updated=True)

    @classmethod
    def add_outerface_to_protocol_id(
            cls, protocol_id: str,
            source_process_name: str, source_port_name: str) -> ProtocolUpdate:
        protocol_model = cls.get_by_id_and_check(protocol_id)
        return cls.add_outerface_to_protocol(
            protocol_model, protocol_model.generate_outerface_name(),
            source_process_name, source_port_name)

    @classmethod
    def add_outerface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str,
            source_process_name: str, source_port_name: str) -> ProtocolUpdate:
        protocol_model.check_is_updatable()

        if protocol_model.is_root_process():
            raise BadRequestException(
                "Cannot add an outerface to the root protocol")
        ioface = protocol_model.add_outerface(
            name, source_process_name, source_port_name)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model,
                                               ioface=ioface,
                                               protocol_updated=True)

    @classmethod
    def delete_interface_of_protocol_id(cls, protocol_id: str, interface_name: str) -> ProtocolUpdate:
        protocol_model = cls.get_by_id_and_check(protocol_id)
        return cls.delete_interface_of_protocol(protocol_model, interface_name)

    @classmethod
    def delete_interface_of_protocol(cls, protocol_model: ProtocolModel, interface_name: str) -> ProtocolUpdate:
        protocol_model.check_is_updatable()
        protocol_model.remove_interface(interface_name)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model, protocol_updated=True)

    @classmethod
    def delete_outerface_of_protocol_id(cls, protocol_id: str, outerface_name: str) -> ProtocolUpdate:
        protocol_model = cls.get_by_id_and_check(protocol_id)
        return cls.delete_outerface_of_protocol(protocol_model, outerface_name)

    @classmethod
    def delete_outerface_of_protocol(cls, protocol_model: ProtocolModel, outerface_name: str) -> ProtocolUpdate:
        protocol_model.check_is_updatable()
        protocol_model.remove_outerface(outerface_name)
        protocol_model.save_graph()

        return cls._on_protocol_object_updated(protocol_model=protocol_model, protocol_updated=True)

    @classmethod
    @transaction()
    def copy_protocol(cls, protocol_model: ProtocolModel) -> ProtocolModel:
        factory = ProtocolGraphFactoryFromType(protocol_model.to_protocol_config_dto())
        new_protocol_model: ProtocolModel = factory.create_protocol_model()
        new_protocol_model.save_full()
        new_protocol_model.reset()
        return new_protocol_model

    ########################## CONFIG #####################

    @classmethod
    @transaction()
    def configure_process(
            cls, protocol_id: str, process_instance_name: str, config_values: ConfigParamsDict) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        process_model: ProcessModel = protocol_model.get_process(process_instance_name)
        process_model.check_is_updatable()

        update_dto: ProtocolUpdate = ProtocolUpdate(protocol=protocol_model, process=process_model)

        cls.configure_process_model(process_model, config_values)

        if process_model.is_auto_run():
            protocol_model.run_auto_run_processes()
            update_dto.protocol_updated = True

        return update_dto

    @classmethod
    @transaction()
    def update_code_params_visitility(cls, protocol_id: str, process_instance_name: str,
                                      new_visibility: ParamSpecVisibilty) -> ProcessDTO:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)
        process_model: ProcessModel = protocol_model.get_process(process_instance_name)

        if EnvAgent.ENV_CONFIG_NAME in process_model.config.get_specs():
            env_spec = process_model.config.get_spec(EnvAgent.ENV_CONFIG_NAME)
            env_spec.visibility = new_visibility
            process_model.config.update_spec(EnvAgent.ENV_CONFIG_NAME, env_spec)

        if EnvAgent.CODE_CONFIG_NAME in process_model.config.get_specs():
            code_spec = process_model.config.get_spec(EnvAgent.CODE_CONFIG_NAME)
            code_spec.visibility = new_visibility
            process_model.config.update_spec(EnvAgent.CODE_CONFIG_NAME, code_spec)

        process_model.config.save()
        return process_model.to_dto()

    @classmethod
    @transaction()
    def configure_process_model(cls, process_model: ProcessModel, config_values: ConfigParamsDict) -> ProtocolUpdate:

        for key in process_model.config.get_specs():
            spec = process_model.config.get_spec(key)
            if spec.visibility == 'private':
                # if spec visibility is private, add it's value to config_value wich basically only has value of public specs
                config_values[key] = process_model.config.get_value(key)

        # set config value and save
        process_model.set_config_values(config_values)
        process_model.config.save()
        # also save the process model because it might have some changes
        return process_model.save()

    @classmethod
    @transaction()
    def set_process_model_config_value(cls, process_model: ProcessModel,
                                       param_name: str, value: ParamValue) -> ProtocolUpdate:
        # set config value and save
        process_model.set_config_value(param_name, value)
        process_model.config.save()
        # also save the process model because it might have some changes
        return process_model.save()

    ########################## SPECIFIC PROCESS #####################

    @classmethod
    def add_input_resource_to_protocol_id(
            cls, protocol_id: str, resource_id: str) -> ProtocolUpdate:
        """ Add a source task to the protocol. Configure it with the resource.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        if protocol_model.scenario:
            cls._check_scenario_circular_reference(resource_id, protocol_model.scenario.id)

        # Create source task model
        source: TaskModel = ProcessFactory.create_source(resource_id)

        # Add the source to the protocol
        return cls.add_process_model_to_protocol(
            protocol_model, source)

    @classmethod
    def add_input_resource_to_process_input(
            cls, protocol_id: str, resource_id: str, process_name: str, input_port_name: str) -> ProtocolUpdate:
        """ Add a source task to the protocol. Configure it with the resource. And add connector
            from source to process
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)
        if protocol_model.scenario:
            cls._check_scenario_circular_reference(resource_id, protocol_model.scenario.id)
        return cls.add_process_connected_to_input(
            protocol_id, InputTask.get_typing_name(),
            process_name, input_port_name, {InputTask.config_name: resource_id})

    @classmethod
    def _check_scenario_circular_reference(cls, new_resource_id: str, scenario_id: str) -> None:
        # Check is there is a circular reference between scenarios (due to partial reset)
        resource_model = ResourceModel.get_by_id_and_check(new_resource_id)
        resource_nav = EntityNavigatorResource(resource_model)

        # check if in the previous scenario of this resource we find the current scenario
        all_previous_exp = resource_nav.get_previous_entities_recursive(
            requested_entities=[EntityType.SCENARIO])
        if all_previous_exp.has_entity(scenario_id):
            raise BadRequestException(
                "Circular reference detected. The selected resource was generated by this scenario or has a resource origin generated by this scenario.")

    @classmethod
    def add_output_task_to_process_ouput(
            cls, protocol_id: str, process_name: str, output_port_name: str) -> ProtocolUpdate:
        """ Add a output task to the protocol. And add connector from process to output
        """

        return cls.add_process_connected_to_output(
            protocol_id, OutputTask.get_typing_name(),
            process_name, output_port_name)

    @classmethod
    @transaction()
    def add_viewer_to_process_output(
            cls, protocol_id: str, process_name: str, output_port_name: str) -> ProtocolUpdate:
        """ Add a view task to the protocol. And add connector from process to view task
        """

        # retrieve the type of the output process port to pre-configure the Viewer
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        existing_process: ProcessModel = protocol_model.get_process(
            process_name)
        existing_out_port: Port = existing_process.out_port(output_port_name)

        viewer_config = {
            Viewer.resource_config_name: existing_out_port.get_default_resource_type().get_typing_name()}

        return cls.add_process_connected_to_output(
            protocol_id, Viewer.get_typing_name(), process_name, output_port_name,
            viewer_config)

    @classmethod
    @transaction()
    def add_scenario_template_to_protocol(
            cls, protocol_id: str, scenario_template_id: str) -> ProtocolUpdate:
        """Insert a sub protocol in the protocol from a template.
        """
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        scenario_template: ScenarioTemplate = ScenarioTemplateService.get_by_id_and_check(
            scenario_template_id)

        # create the sub protocol from the template
        sub_protocol = scenario_template.generate_protocol_model()

        # replace Input and Output with iofaces
        sub_protocol.replace_io_process_with_ioface()

        return cls.add_process_model_to_protocol(protocol_model, sub_protocol)

    ########################## LAYOUT #####################

    @classmethod
    def save_layout(cls, protocol_id: str, layout_dict: ProtocolLayoutDTO) -> None:
        layout = ProtocolLayout(layout_dict)
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout = layout
        protocol_model.save()

    @classmethod
    def save_process_layout(cls, protocol_id: str, process_instance_name: str, layout: ProcessLayoutDTO) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout.set_process(process_instance_name, layout)
        protocol_model.save()

    @classmethod
    def save_interface_layout(cls, protocol_id: str, interface_name: str, layout: ProcessLayoutDTO) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout.set_interface(interface_name, layout)
        protocol_model.save()

    @classmethod
    def save_outerface_layout(cls, protocol_id: str, outerface_name: str, layout: ProcessLayoutDTO) -> None:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        protocol_model.layout.set_outerface(outerface_name, layout)
        protocol_model.save()

    ########################## DYNAMIC PORTS #####################

    @classmethod
    def add_dynamic_input_port_to_process(
            cls, protocol_id: str, process_name: str, io_spec_dto: IOSpecDTO = None) -> ProtocolUpdate:
        return cls._add_dynamic_port_to_process(protocol_id, process_name, 'input', io_spec_dto)

    @classmethod
    def add_dynamic_output_port_to_process(
            cls, protocol_id: str, process_name: str, io_spec_dto: IOSpecDTO = None) -> ProtocolUpdate:
        return cls._add_dynamic_port_to_process(protocol_id, process_name, 'output', io_spec_dto)

    @classmethod
    def _add_dynamic_port_to_process(
            cls, protocol_id: str, process_name: str, port_type: Literal['input', 'output'],
            io_spec_dto: IOSpecDTO = None) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        process_model = protocol_model.get_process(process_name)

        process_model.check_is_updatable()

        io: IO = process_model.inputs if port_type == 'input' else process_model.outputs

        # generate the default spec and add port
        io_specs: Union[DynamicInputs, DynamicOutputs] = io.get_specs()
        io_spec = IOSpec.from_dto(io_spec_dto) if io_spec_dto is not None else io_specs.get_default_spec()
        io.create_port(StringHelper.generate_uuid(), io_spec)

        process_model.save()
        new_update = ProtocolUpdate(protocol=protocol_model, protocol_updated=False,
                                    process=process_model)
        return new_update

    @classmethod
    def delete_dynamic_input_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str) -> ProtocolUpdate:
        return cls._delete_dynamic_port_of_process(protocol_id, process_name, port_name, 'input')

    @classmethod
    def delete_dynamic_output_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str) -> ProtocolUpdate:
        return cls._delete_dynamic_port_of_process(protocol_id, process_name, port_name, 'output')

    @classmethod
    @transaction()
    def _delete_dynamic_port_of_process(cls, protocol_id: str, process_name: str,
                                        port_name: str, port_type: Literal['input', 'output']) -> ProtocolUpdate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        process_model: ProcessModel = protocol_model.get_process(process_name)
        process_model.check_is_updatable()

        io: IO = process_model.inputs if port_type == 'input' else process_model.outputs

        if port_type == 'input':
            protocol_model.delete_connector_from_right(process_name, port_name)
        else:
            protocol_model.delete_connectors_from_left(process_name, port_name)
        protocol_model.save_graph()

        io.remove_port(port_name)
        process_model.save()
        new_update = ProtocolUpdate(protocol=protocol_model, protocol_updated=True,
                                    process=process_model)
        return new_update

    @classmethod
    def update_dynamic_input_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str, io_spec: IOSpecDTO) -> ProtocolUpdate:
        return cls._update_dynamic_port_of_process(protocol_id, process_name, port_name, io_spec, 'input')

    @classmethod
    def update_dynamic_output_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str, io_spec: IOSpecDTO) -> ProtocolUpdate:
        return cls._update_dynamic_port_of_process(protocol_id, process_name, port_name, io_spec, 'output')

    @classmethod
    @transaction()
    def _update_dynamic_port_of_process(
            cls, protocol_id: str, process_name: str, port_name: str, io_spec_dto: IOSpecDTO,
            port_type: Literal['input', 'output']) -> ProtocolUpdate:

        io_spec_class: Type[IOSpec] = InputSpec if port_type == 'input' else OutputSpec
        io_spec: IOSpec = io_spec_class.from_dto(io_spec_dto)

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        process_model: ProcessModel = protocol_model.get_process(process_name)
        process_model.check_is_updatable()
        io: IO = process_model.inputs if port_type == 'input' else process_model.outputs

        if not io.is_dynamic:
            raise BadRequestException(
                f"The process does not support dynamic {port_type} ports")

        io.update_port(port_name, io_spec)
        process_model.save()

        new_update = ProtocolUpdate(protocol=protocol_model, protocol_updated=False,
                                    process=process_model)
        return new_update

    ########################## OTHERS  #####################

    @classmethod
    def rename_process(cls, protocol_id: str, process_instance_name: str,
                       custom_name: str) -> ProcessModel:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_model: ProcessModel = protocol_model.get_process(process_instance_name)
        process_model.name = custom_name
        process_model.save()

        return process_model

    @classmethod
    def update_process_style(cls, protocol_id, process_instance_name: str,
                             style: TypingStyle) -> ProcessModel:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)
        process_model: ProcessModel = protocol_model.get_process(process_instance_name)
        process_model.style = style
        process_model.save()

        return process_model

    ########################## PROTOCOL TEMPLATE #####################

    @classmethod
    def create_scenario_template_from_id(
            cls, protocol_id: str, name: str, description: RichTextDTO = None) -> ScenarioTemplate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)
        return ScenarioTemplateService.create_from_protocol(protocol=protocol_model,
                                                            name=name, description=description)

    @classmethod
    def create_protocol_model_from_template(cls, scenario_template: ScenarioTemplate) -> ProtocolModel:
        return cls.create_protocol_model_from_graph(scenario_template.get_template())

    @classmethod
    def create_protocol_model_from_graph(cls, graph: ProtocolGraphConfigDTO) -> ProtocolModel:
        factory = ProtocolGraphFactoryFromType(graph)

        protocol: ProtocolModel = factory.create_protocol_model()

        protocol.save_full()
        return protocol

    @classmethod
    def generate_scenario_template(cls, protocol_id: str) -> ScenarioTemplate:
        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(
            protocol_id)

        if not protocol_model.scenario:
            raise BadRequestException(
                "Cannot download a protocol without scenario")

        return ScenarioTemplateFactory.from_protocol_model(protocol_model,
                                                           protocol_model.scenario.title,
                                                           protocol_model.scenario.description)

    ########################## COMMUNITY #####################

    @classmethod
    @transaction()
    def add_agent_to_protocol_id_by_agent_version_id(
            cls, protocol_id: str, agent_version_id: str) -> ProtocolUpdate:
        community_agent_version: CommunityAgentVersionDTO = CommunityService.get_community_agent_version(
            agent_version_id)

        return cls.add_community_agent_version_to_protocol_id(protocol_id, community_agent_version)

    @classmethod
    @transaction()
    def add_community_agent_version_to_protocol_id(
            cls, protocol_id: str, community_agent_version: CommunityAgentVersionDTO) -> ProtocolUpdate:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_typing: Typing = TypingManager.get_typing_from_name_and_check(community_agent_version.type)

        agent_type: Type[Process] = process_typing.get_type()

        params = {}
        if community_agent_version.params:
            params = community_agent_version.params['values']

        # Build the config params dict with specs values
        config_params: ConfigParamsDict
        if issubclass(agent_type, PyAgent):
            config_params = agent_type.build_config_params_dict(
                code=community_agent_version.code,
                params=params)
        elif issubclass(agent_type, EnvAgent):
            config_params = agent_type.build_config_params_dict(
                code=community_agent_version.code,
                params=params,
                env=community_agent_version.environment)
        elif issubclass(agent_type, StreamlitAgent):
            config_params = agent_type.build_config_params_dict(code=community_agent_version.code, params=params)
        else:
            raise BadRequestException("The agent type is not supported")

        # create the process and add it to the protocol
        process_model: ProcessModel = ProcessFactory.create_task_model_from_type(
            task_type=process_typing.get_type(),
            config_params=config_params,
            community_agent_version_id=community_agent_version.id,
            name=community_agent_version.agent.title,
            style=community_agent_version.style
        )

        # Get the dynamic param of the newly created agent process model
        dynamic_param_spec: DynamicParam = cls.get_process_dynamic_param_spec(
            process_model=process_model, config_spec_name=EnvAgent.PARAMS_CONFIG_NAME)

        for param_name, param_value in community_agent_version.params['specs'].items():
            # for each values in specs, add the good spec type to the dynamic param
            dynamic_param_spec.add_spec(param_name, ParamSpecDTO.from_json(param_value))

        # update the config spec 'params'
        process_model.config.update_spec(EnvAgent.PARAMS_CONFIG_NAME, dynamic_param_spec)

        # set the default visibility of config spec 'code' to 'private'
        config_code_spec = process_model.config.get_spec(EnvAgent.CODE_CONFIG_NAME)
        config_code_spec.visibility = 'private'
        process_model.config.update_spec(EnvAgent.CODE_CONFIG_NAME, config_code_spec)

        if (issubclass(agent_type, EnvAgent)):
            # set the default visibility of config spec 'env' to 'private'
            config_env_spec = process_model.config.get_spec(EnvAgent.ENV_CONFIG_NAME)
            config_env_spec.visibility = 'private'
            process_model.config.update_spec(EnvAgent.ENV_CONFIG_NAME, config_env_spec)

        protocol_update = cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=process_model)

        # TODO TO IMPROVE WHEN UPDATING AGENT CONFIG
        if protocol_update.process.inputs.is_dynamic:
            for port in list(protocol_update.process.inputs.ports.keys()):
                protocol_update = cls.delete_dynamic_input_port_of_process(
                    protocol_id, protocol_update.process.instance_name, port)

            for io_spec in list(community_agent_version.input_specs.specs.values()):
                protocol_update = cls.add_dynamic_input_port_to_process(
                    protocol_id, protocol_update.process.instance_name, io_spec)

        if protocol_update.process.outputs.is_dynamic:
            for port in list(protocol_update.process.outputs.ports.keys()):
                protocol_update = cls.delete_dynamic_output_port_of_process(
                    protocol_id, protocol_update.process.instance_name, port)

            for io_spec in list(community_agent_version.output_specs.specs.values()):
                protocol_update = cls.add_dynamic_output_port_to_process(
                    protocol_id, protocol_update.process.instance_name, io_spec)

        return protocol_update

    @classmethod
    @transaction()
    def get_community_available_space(cls) -> Any:
        return CommunityService.get_community_available_space()

    @classmethod
    @transaction()
    def get_community_available_agents(
            cls, spaces_filter: List[str],
            title_filter: str, personal_only: bool, page: int, number_of_items_per_page: int) -> Any:
        return CommunityService.get_community_available_agents(
            spaces_filter, title_filter, personal_only, page, number_of_items_per_page)

    @classmethod
    def get_community_agent(cls, agent_version_id: str) -> CommunityAgentDTO:
        return CommunityService.get_community_agent(agent_version_id)

    @classmethod
    def create_community_agent(
            cls, process_id: str, form_data: CommunityCreateAgentDTO) -> CommunityAgentVersionCreateResDTO:
        version_file: CommunityAgentFileDTO = AgentFactory.generate_agent_file_from_agent_id(process_id)
        return CommunityService.create_community_agent(version_file, form_data)

    @classmethod
    def fork_community_agent(cls, process_id: str, form_data: CommunityCreateAgentDTO, agent_version_id: str) -> CommunityAgentVersionCreateResDTO:
        version_file: CommunityAgentFileDTO = AgentFactory.generate_agent_file_from_agent_id(process_id)
        return CommunityService.fork_community_agent(version_file, form_data, agent_version_id)

    @classmethod
    def create_community_agent_version(
            cls, process_id: str, agent_id: str) -> CommunityAgentVersionCreateResDTO:
        version_file: CommunityAgentFileDTO = AgentFactory.generate_agent_file_from_agent_id(process_id)
        return CommunityService.create_community_agent_version(version_file, agent_id)

    ########################## DYNAMIC PARAM #####################
    @classmethod
    def get_and_check_dynamic_param(cls, process_model: ProcessModel, config_spec_name: str) -> DynamicParam:
        process_model.check_is_updatable()
        dynamic_param_spec: DynamicParam = process_model.config.get_spec(config_spec_name)

        if not isinstance(dynamic_param_spec, DynamicParam):
            raise BadRequestException("The process does not support adding dynamic param specs")

        return dynamic_param_spec

    @classmethod
    def update_dynamic_param_config_spec(
            cls, process_model: ProcessModel, config_spec_name: str, dynamic_param_spec: DynamicParam,
            values: Dict[str, Any] = None) -> ConfigSimpleDTO:
        process_model.config.update_spec(config_spec_name, dynamic_param_spec)

        if values:
            process_model.config.set_value(config_spec_name, values, skip_validate=True)

        process_model.config = process_model.config.save()

        process_model.save()

        return process_model.config.to_simple_dto()

    @classmethod
    def add_dynamic_param_spec_of_process(
            cls, protocol_id: str, process_name: str, config_spec_name: str, param_name: str, spec_dto: ParamSpecDTO) -> ConfigSimpleDTO:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_model = protocol_model.get_process(process_name)

        dynamic_param_spec: DynamicParam = cls.get_and_check_dynamic_param(
            process_model=process_model, config_spec_name=config_spec_name)

        dynamic_param_spec.add_spec(param_name, spec_dto)

        return cls.update_dynamic_param_config_spec(process_model, config_spec_name, dynamic_param_spec)

    @classmethod
    def update_dynamic_param_spec_of_process(
            cls, protocol_id: str, process_name: str, config_spec_name: str, param_name: str, spec_dto: ParamSpecDTO) -> ConfigSimpleDTO:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_model = protocol_model.get_process(process_name)

        dynamic_param_spec: DynamicParam = cls.get_and_check_dynamic_param(
            process_model=process_model, config_spec_name=config_spec_name)

        if spec_dto.type != dynamic_param_spec.specs[param_name].get_str_type():
            value = process_model.config.get_value(config_spec_name)
            if param_name in value:
                value[param_name] = spec_dto.default_value
                process_model.config.set_value(config_spec_name, value, skip_validate=True)

        dynamic_param_spec.update_spec(param_name, spec_dto)

        return cls.update_dynamic_param_config_spec(process_model, config_spec_name, dynamic_param_spec)

    @classmethod
    def rename_and_update_dynamic_param_spec_of_process(
            cls, protocol_id: str, process_name: str, config_spec_name: str, param_name: str, new_param_name: str,
            spec_dto: ParamSpecDTO) -> ConfigSimpleDTO:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_model = protocol_model.get_process(process_name)

        dynamic_param_spec: DynamicParam = cls.get_and_check_dynamic_param(
            process_model=process_model, config_spec_name=config_spec_name)

        values = process_model.config.get_value(config_spec_name)
        if spec_dto.type != dynamic_param_spec.specs[param_name].get_str_type() and param_name in values:
            values[new_param_name] = spec_dto.default_value
        if param_name in values:
            del values[param_name]

        dynamic_param_spec.rename_and_update_spec(param_name, new_param_name, spec_dto)

        return cls.update_dynamic_param_config_spec(process_model, config_spec_name, dynamic_param_spec, values)

    @classmethod
    def remove_dynamic_param_spec_of_process(
            cls, protocol_id: str, process_name: str, config_spec_name: str, param_name: str) -> ConfigSimpleDTO:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_model = protocol_model.get_process(process_name)

        dynamic_param_spec: DynamicParam = cls.get_and_check_dynamic_param(
            process_model=process_model, config_spec_name=config_spec_name)

        values = process_model.config.get_value(config_spec_name)

        dynamic_param_spec.remove_spec(param_name)

        if param_name in values:
            del values[param_name]

        return cls.update_dynamic_param_config_spec(process_model, config_spec_name, dynamic_param_spec, values)

    @classmethod
    def get_process_dynamic_param_spec(cls, process_model: ProcessModel, config_spec_name: str) -> DynamicParam:

        dynamic_param_spec: DynamicParam = DynamicParam.load_from_dto(
            ParamSpecDTO.from_json(process_model.config.data.get('specs').get(config_spec_name)))

        if dynamic_param_spec is None:
            raise BadRequestException("The process does not support dynamic params")

        return dynamic_param_spec

    @classmethod
    def get_dynamic_param_allowed_param_spec_types(
            cls, protocol_id: str, process_name: str) -> DynamicParamAllowedSpecsDict:

        protocol_model: ProtocolModel = ProtocolModel.get_by_id_and_check(protocol_id)

        process_model = protocol_model.get_process(process_name)

        if process_model.process_typing_name == PyAgent.get_typing_name():
            return ParamSpecHelper.get_dynamic_param_allowed_param_spec_types(True)

        return ParamSpecHelper.get_dynamic_param_allowed_param_spec_types()
