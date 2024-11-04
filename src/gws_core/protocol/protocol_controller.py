

import threading
from typing import Any, Optional

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.entity_navigator.entity_navigator_dto import ImpactResultDTO
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_dto import ProcessDTO
from gws_core.protocol.protocol_dto import (AddConnectorDTO, ProtocolDTO,
                                            ProtocolUpdateDTO)
from gws_core.protocol.protocol_layout import (ProcessLayoutDTO,
                                               ProtocolLayoutDTO)
from gws_core.scenario_template.scenario_template_dto import \
    ScenarioTemplateDTO

from ..community.community_dto import (CommunityAgentDTO,
                                       CommunityCreateAgentDTO,
                                       CommunityGetAgentsBody)
from ..core_controller import core_app
from ..user.auth_service import AuthService
from .protocol_service import ProtocolService

# use to prevent multiple request to modify a protocol at the same time, they will be queued
# this is because protocol load can be long if there is a lot of process so second request can start
# before the first one is finished so this will break the protocol processes.
# this is not the best solution but it's a quick fix
update_lock = threading.Lock()


@core_app.get("/protocol/{id_}", tags=["Protocol"], summary="Get a protocol")
def get_a_protocol(id_: str,
                   _=Depends(AuthService.check_user_access_token)) -> ProtocolDTO:
    """
    Retrieve a protocol

    - **id_**: the id_ of the protocol
    """

    return ProtocolService.get_by_id_and_check(id_).to_protocol_dto()


@core_app.post("/protocol/{id_}/add-process/{process_typing_name}", tags=["Protocol"],
               summary="Add a process to a protocol")
def add_process(id_: str,
                process_typing_name: str,
                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_process_to_protocol_id(
            protocol_id=id_,
            process_typing_name=process_typing_name
        ).to_dto()


@core_app.post("/protocol/{id_}/add-empty-protocol", tags=["Protocol"],
               summary="Add an empty protocol to a protocol")
def add_empty_protocol(id_: str,
                       _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_empty_protocol_to_protocol_id(
            protocol_id=id_,
        ).to_dto()


@core_app.post("/protocol/{id_}/duplicate-process/{process_instance_name}", tags=["Protocol"],
               summary="Duplicate process in protocol")
def duplicate_process(id_: str,
                      process_instance_name: str,
                      _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a duplication of a process to a protocol
    """

    with update_lock:
        return ProtocolService.duplicate_process_to_protocol_id(
            protocol_id=id_,
            process_instance_name=process_instance_name
        ).to_dto()


@core_app.post("/protocol/{id_}/add-community-agent/{agent_version_id}", tags=["Protocol"],
               summary="Add a community agent to a protocol")
def add_community_agent(id_: str,
                        agent_version_id: str,
                        _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a constellab community agent to a protocol
    """
    with update_lock:
        return ProtocolService.add_agent_to_protocol_id_by_agent_version_id(id_, agent_version_id).to_dto()


@core_app.post("/protocol/get-community-available-spaces", tags=["Protocol"],
               summary="Get community spaces available for the protocol")
def get_community_available_space(_=Depends(AuthService.check_user_access_token)) -> Any:
    """
    Add a constellab community agent to a protocol
    """
    return ProtocolService.get_community_available_space()


@core_app.post("/protocol/get-community-available-agents", tags=["Protocol"],
               summary="Get community agents available for the protocol")
def get_community_available_agents(page: int,
                                   number_of_items_per_page: int,
                                   body: CommunityGetAgentsBody,
                                   _=Depends(AuthService.check_user_access_token)) -> Any:
    """
    Add a constellab community agent to a protocol
    """
    return ProtocolService.get_community_available_agents(
        body.spacesFilter, body.titleFilter, body.personalOnly,
        page, number_of_items_per_page)


@core_app.get("/protocol/get-current-agent/{agent_version_id}", tags=["Protocol"],
              summary="Get community agent by agent version id")
def get_community_agent(agent_version_id: str,
                        _=Depends(AuthService.check_user_access_token)) -> CommunityAgentDTO:
    return ProtocolService.get_community_agent(agent_version_id)


@core_app.post("/protocol/{id}/create-community-agent", tags=["Protocol"],
               summary="Create a community agent in community")
def create_community_agent(id: str,
                           form_data: CommunityCreateAgentDTO,
                           _=Depends(AuthService.check_user_access_token)) -> Any:
    """
    Create a constellab community agent
    """
    return ProtocolService.create_community_agent(id, form_data)


@core_app.post("/protocol/{id}/fork-community-agent/{agent_version_id}", tags=["Protocol"],
               summary="Fork into a new community agent")
def fork_community_agent(id: str,
                         form_data: CommunityCreateAgentDTO,
                         agent_version_id: str,
                         _=Depends(AuthService.check_user_access_token)) -> Any:
    """
    Create a constellab community agent
    """
    return ProtocolService.fork_community_agent(id, form_data, agent_version_id)


@core_app.post("/protocol/{id}/add-version-to-community-agent/{agent_id}", tags=["Protocol"],
               summary="Create a community agent in community")
def create_new_community_agent_version(id: str,
                                       agent_id: str,
                                       _=Depends(AuthService.check_user_access_token)) -> Any:
    """
    Create a new constellab community agent version
    """
    return ProtocolService.create_community_agent_version(id, agent_id)


@core_app.post("/protocol/{id_}/add-process/{process_typing_name}/connected-to-output/{process_name}/{port_name}",
               tags=["Protocol"],
               summary="Add a process to a protocol connected to a selected output")
def add_process_connected_to_output(id_: str,
                                    process_typing_name: str,
                                    process_name: str,
                                    port_name: str,
                                    _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a process to a protocol
    """
    with update_lock:
        return ProtocolService.add_process_connected_to_output(
            protocol_id=id_,
            process_typing_name=process_typing_name,
            output_process_name=process_name,
            output_port_name=port_name
        ).to_dto()


@core_app.post("/protocol/{id_}/add-process/{process_typing_name}/connected-to-input/{process_name}/{port_name}",
               tags=["Protocol"],
               summary="Add a process to a protocol connected to a selected input")
def add_process_connected_to_input(id_: str,
                                   process_typing_name: str,
                                   process_name: str,
                                   port_name: str,
                                   _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a process to a protocol
    """
    with update_lock:
        return ProtocolService.add_process_connected_to_input(
            protocol_id=id_,
            process_typing_name=process_typing_name,
            input_process_name=process_name,
            input_port_name=port_name
        ).to_dto()


@core_app.delete("/protocol/{id_}/process/{process_instance_name}", tags=["Protocol"],
                 summary="Delete a process of a protocol")
def delete_process(id_: str,
                   process_instance_name: str,
                   _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_process_of_protocol_id(
            protocol_id=id_,
            process_instance_name=process_instance_name
        ).to_dto()


@core_app.put("/protocol/{id_}/process/{process_instance_name}/reset", tags=["Protocol"],
              summary="Reset a process of a protocol")
def reset_process(id_: str,
                  process_instance_name: str,
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return EntityNavigatorService.reset_process_of_protocol_id(
            protocol_id=id_,
            process_instance_name=process_instance_name).to_dto()


@core_app.get("/protocol/{id_}/process/{process_instance_name}/reset/check-impact", tags=["Protocol"],
              summary="Reset a process of a protocol")
def check_impact_for_process_reset(id_: str,
                                   process_instance_name: str,
                                   _=Depends(AuthService.check_user_access_token)) -> ImpactResultDTO:
    return EntityNavigatorService.check_impact_for_process_reset(
        protocol_id=id_,
        process_instance_name=process_instance_name).to_dto()


@core_app.put("/protocol/{id_}/process/{process_instance_name}/run", tags=["Protocol"],
              summary="Run a process of a protocol")
def run_process(id_: str,
                process_instance_name: str,
                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    return ProtocolService.run_process(
        protocol_id=id_,
        process_instance_name=process_instance_name
    ).to_dto()


########################## CONNECTORS #####################


@core_app.post("/protocol/{id_}/connector", tags=["Protocol"],
               summary="Add a connector between 2 process of a protocol")
def add_connector(id_: str,
                  connector: AddConnectorDTO,
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_connector_to_protocol_id(
            protocol_id=id_,
            from_process_name=connector.output_process_name,
            from_port_name=connector.output_port_name,
            to_process_name=connector.input_process_name,
            to_port_name=connector.input_port_name,
        ).to_dto()


@core_app.delete("/protocol/{id_}/connector/{dest_process_name}/{dest_process_port_name}", tags=["Protocol"],
                 summary="Delete a connector in a protocol")
def delete_connector(id_: str,
                     dest_process_name: str,
                     dest_process_port_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_connector_of_protocol(
            protocol_id=id_,
            dest_process_name=dest_process_name,
            dest_process_port_name=dest_process_port_name
        ).to_dto()


########################## CONFIG #####################
@core_app.put("/protocol/{id_}/process/{process_instance_name}/config", tags=["Protocol"],
              summary="Configure a process of a protocol")
def configure_process(id_: str,
                      process_instance_name: str,
                      config_values: dict,
                      _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.configure_process(
            protocol_id=id_, process_instance_name=process_instance_name, config_values=config_values).to_dto()

########################## INTERFACE / OUTERFACE #####################


@core_app.post("/protocol/{id_}/interface/{target_process_name}/{target_port_name}", tags=["Protocol"],
               summary="Add an interface")
def add_interface(id_: str,
                  target_process_name: str,
                  target_port_name: str,
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_interface_to_protocol_id(
            id_, target_process_name, target_port_name).to_dto()


@core_app.post("/protocol/{id_}/outerface/{target_process_name}/{target_port_name}", tags=["Protocol"],
               summary="Add an outerface")
def add_outerface(id_: str,
                  target_process_name: str,
                  target_port_name: str,
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_outerface_to_protocol_id(
            id_, target_process_name, target_port_name).to_dto()


@core_app.delete("/protocol/{id_}/interface/{interface_name}", tags=["Protocol"],
                 summary="Delete an interface")
def delete_interface(id_: str,
                     interface_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_interface_of_protocol_id(
            id_, interface_name).to_dto()


@core_app.delete("/protocol/{id_}/outerface/{outerface_name}", tags=["Protocol"],
                 summary="Delete an outerface")
def delete_outerface(id_: str,
                     outerface_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_outerface_of_protocol_id(
            id_, outerface_name).to_dto()


########################## SPECIFIC PROCESS #####################

@core_app.post("/protocol/{id_}/add-source/{resource_id}/{process_name}/{input_port_name}", tags=["Protocol"],
               summary="Add a configured source link to a process' input")
def add_source_to_process_input(id_: str,
                                resource_id: str,
                                process_name: str,
                                input_port_name: str,
                                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_source_to_process_input(
            protocol_id=id_, resource_id=resource_id, process_name=process_name,
            input_port_name=input_port_name).to_dto()


@core_app.post("/protocol/{id_}/add-source/{resource_id}", tags=["Protocol"],
               summary="Add a configured source link to a process' input")
def add_source_to_protocol(id_: str,
                           resource_id: str,
                           _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_source_to_protocol_id(
            protocol_id=id_, resource_id=resource_id).to_dto()


@core_app.post("/protocol/{id_}/add-sink/{process_name}/{output_port_name}", tags=["Protocol"],
               summary="Add a sink link a process' output")
def add_sink_to_process_ouput(id_: str,
                              process_name: str,
                              output_port_name: str,
                              _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_sink_to_process_ouput(
            protocol_id=id_, process_name=process_name, output_port_name=output_port_name).to_dto()


@core_app.post("/protocol/{id_}/add-viewer/{process_name}/{output_port_name}", tags=["Protocol"],
               summary="Add a viewer link a process' output")
def add_viewer_to_process_ouput(id_: str,
                                process_name: str,
                                output_port_name: str,
                                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_viewer_to_process_output(
            protocol_id=id_, process_name=process_name, output_port_name=output_port_name).to_dto()


@core_app.post("/protocol/{id_}/add-template/{scenario_template_id}", tags=["Protocol"],
               summary="Add a viewer link a process' output")
def add_scenario_template_to_protocol(id_: str,
                                      scenario_template_id: str,
                                      _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_scenario_template_to_protocol(
            protocol_id=id_, scenario_template_id=scenario_template_id).to_dto()


########################## LAYOUT #####################
@core_app.put("/protocol/{id_}/layout", tags=["Protocol"],
              summary="Save the layout of a protocol")
def save_layout(id_: str,
                layout_dict: ProtocolLayoutDTO,
                _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_layout(id_, layout_dict)


@core_app.put("/protocol/{id_}/layout/process/{process_name}", tags=["Protocol"],
              summary="Save the layout of 1 process in a protocol")
def save_process_layout(id_: str,
                        process_name: str,
                        layout_dict: ProcessLayoutDTO,
                        _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_process_layout(id_, process_name, layout_dict)


@core_app.put("/protocol/{id_}/layout/interface/{interface_name}", tags=["Protocol"],
              summary="Save the layout of 1 interface in a protocol")
def save_interface_layout(id_: str,
                          interface_name: str,
                          layout_dict: ProcessLayoutDTO,
                          _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_interface_layout(id_, interface_name, layout_dict)


@core_app.put("/protocol/{id_}/layout/outerface/{outerface_name}", tags=["Protocol"],
              summary="Save the layout of 1 outerface in a protocol")
def save_outerface_layout(id_: str,
                          outerface_name: str,
                          layout_dict: ProcessLayoutDTO,
                          _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_outerface_layout(id_, outerface_name, layout_dict)


########################## DYNAMIC PORTS #####################
@core_app.post("/protocol/{id_}/process/{process_name}/dynamic-input", tags=["Protocol"],
               summary="Add a dynamic port to a process")
def add_dynamic_input_port_to_process(id_: str,
                                      process_name: str,
                                      _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_dynamic_input_port_to_process(
            id_, process_name).to_dto()


@core_app.post("/protocol/{id_}/process/{process_name}/dynamic-output", tags=["Protocol"],
               summary="Add a dynamic port to a process")
def add_dynamic_output_port_to_process(id_: str,
                                       process_name: str,
                                       _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_dynamic_output_port_to_process(
            id_, process_name).to_dto()


@core_app.delete("/protocol/{id_}/process/{process_name}/dynamic-input/{port_name}", tags=["Protocol"],
                 summary="Delete a dynamic port of a process")
def delete_dynamic_input_port_of_process(id_: str,
                                         process_name: str,
                                         port_name: str,
                                         _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_dynamic_input_port_of_process(id_, process_name, port_name).to_dto()


@core_app.delete("/protocol/{id_}/process/{process_name}/dynamic-output/{port_name}", tags=["Protocol"],
                 summary="Delete a dynamic port of a process")
def delete_dynamic_output_port_of_process(id_: str,
                                          process_name: str,
                                          port_name: str,
                                          _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_dynamic_output_port_of_process(id_, process_name, port_name).to_dto()


@core_app.put("/protocol/{id_}/process/{process_name}/dynamic-input/{port_name}", tags=["Protocol"],
              summary="Update a dynamic port of a process")
def update_dynamic_input_port_of_process(id_: str,
                                         process_name: str,
                                         port_name: str,
                                         io_spec: IOSpecDTO,
                                         _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    print(process_name, port_name, io_spec)
    with update_lock:
        return ProtocolService.update_dynamic_input_port_of_process(id_, process_name, port_name, io_spec).to_dto()


@core_app.put("/protocol/{id_}/process/{process_name}/dynamic-output/{port_name}", tags=["Protocol"],
              summary="Update a dynamic port of a process")
def update_dynamic_output_port_of_process(id_: str,
                                          process_name: str,
                                          port_name: str,
                                          io_spec: IOSpecDTO,
                                          _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.update_dynamic_output_port_of_process(id_, process_name, port_name, io_spec).to_dto()


########################## OTHERS  #####################
class UpdateProcessNameDTO(BaseModelDTO):
    new_name: str


@core_app.put("/protocol/{id_}/process/{process_name}/rename", tags=["Protocol"],
              summary="Rename a process of a protocol")
def rename_process(id_: str,
                   process_name: str,
                   new_name: UpdateProcessNameDTO,
                   _=Depends(AuthService.check_user_access_token)) -> ProcessDTO:
    with update_lock:
        return ProtocolService.rename_process(id_, process_name,
                                              new_name.new_name).to_dto()


@core_app.put("/protocol/{id_}/process/{process_name}/style", tags=["Protocol"],
              summary="Update the style of a process of a protocol")
def update_process_style(id_: str,
                         process_name: str,
                         style: TypingStyle,
                         _=Depends(AuthService.check_user_access_token)) -> ProcessDTO:
    with update_lock:
        return ProtocolService.update_process_style(id_, process_name,
                                                    style).to_dto()

########################## TEMPLATE #####################


class CreateScenarioTemplate(BaseModelDTO):
    name: str = None
    description: Optional[dict] = None


@core_app.post("/protocol/{id_}/template", tags=["Protocol"],
               summary="Create a template from a protocol")
def create_template(id_: str,
                    template: CreateScenarioTemplate,
                    _=Depends(AuthService.check_user_access_token)) -> ScenarioTemplateDTO:
    return ProtocolService.create_scenario_template_from_id(id_, template.name, template.description).to_dto()


@core_app.get("/protocol/{id_}/template/download", tags=["Protocol"],
              summary="Download a template from a protocol")
def download_template(id_: str,
                      _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    template = ProtocolService.generate_scenario_template(id_)
    return ResponseHelper.create_file_response_from_str(template.to_export_dto().json(), template.name + '.json')
