# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import threading
from typing import Optional

from fastapi import Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.io.io_spec import IOSpecDTO
from gws_core.protocol.protocol_dto import (AddConnectorDTO, ProtocolDTO,
                                            ProtocolUpdateDTO)
from gws_core.protocol_template.protocol_template_dto import \
    ProtocolTemplateDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .protocol_service import ProtocolService

# use to prevent multiple request to modify a protocol at the same time, they will be queued
# this is because protocol load can be long if there is a lot of process so second request can start
# before the first one is finished so this will break the protocol processes.
# this is not the best solution but it's a quick fix
update_lock = threading.Lock()


@core_app.get("/protocol/{id}", tags=["Protocol"], summary="Get a protocol")
def get_a_protocol(id: str,
                   _=Depends(AuthService.check_user_access_token)) -> ProtocolDTO:
    """
    Retrieve a protocol

    - **id**: the id of the protocol
    """

    return ProtocolService.get_protocol_by_id(id=id).to_protocol_dto()


@core_app.post("/protocol/{id}/add-process/{process_typing_name}", tags=["Protocol"],
               summary="Add a process to a protocol")
def add_process(id: str,
                process_typing_name: str,
                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a process to a protocol
    """

    with update_lock:
        return ProtocolService.add_process_to_protocol_id(
            protocol_id=id,
            process_typing_name=process_typing_name
        ).to_dto()


@core_app.post("/protocol/{id}/add-process/{process_typing_name}/connected-to-output/{process_name}/{port_name}",
               tags=["Protocol"],
               summary="Add a process to a protocol connected to a selected output")
def add_process_connected_to_output(id: str,
                                    process_typing_name: str,
                                    process_name: str,
                                    port_name: str,
                                    _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a process to a protocol
    """
    with update_lock:
        return ProtocolService.add_process_connected_to_output(
            protocol_id=id,
            process_typing_name=process_typing_name,
            output_process_name=process_name,
            output_port_name=port_name
        ).to_dto()


@core_app.post("/protocol/{id}/add-process/{process_typing_name}/connected-to-input/{process_name}/{port_name}",
               tags=["Protocol"],
               summary="Add a process to a protocol connected to a selected input")
def add_process_connected_to_input(id: str,
                                   process_typing_name: str,
                                   process_name: str,
                                   port_name: str,
                                   _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    """
    Add a process to a protocol
    """
    with update_lock:
        return ProtocolService.add_process_connected_to_input(
            protocol_id=id,
            process_typing_name=process_typing_name,
            input_process_name=process_name,
            input_port_name=port_name
        ).to_dto()


@core_app.delete("/protocol/{id}/process/{process_instance_name}", tags=["Protocol"],
                 summary="Delete a process of a protocol")
def delete_process(id: str,
                   process_instance_name: str,
                   _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_process_of_protocol_id(
            protocol_id=id,
            process_instance_name=process_instance_name
        ).to_dto()


@core_app.put("/protocol/{id}/process/{process_instance_name}/reset", tags=["Protocol"],
              summary="Reset a process of a protocol")
def reset_process(id: str,
                  process_instance_name: str,
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.reset_process_of_protocol_id(
            protocol_id=id,
            process_instance_name=process_instance_name
        ).to_dto()


@core_app.put("/protocol/{id}/process/{process_instance_name}/run", tags=["Protocol"],
              summary="Run a process of a protocol")
def run_process(id: str,
                process_instance_name: str,
                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    return ProtocolService.run_process(
        protocol_id=id,
        process_instance_name=process_instance_name
    ).to_dto()


########################## CONNECTORS #####################


@core_app.post("/protocol/{id}/connector", tags=["Protocol"],
               summary="Add a connector between 2 process of a protocol")
def add_connector(id: str,
                  add_connector: AddConnectorDTO,
                  _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_connector_to_protocol_id(
            protocol_id=id,
            from_process_name=add_connector.output_process_name,
            from_port_name=add_connector.output_port_name,
            to_process_name=add_connector.input_process_name,
            to_port_name=add_connector.input_port_name,
        ).to_dto()


@core_app.delete("/protocol/{id}/connector/{dest_process_name}/{dest_process_port_name}", tags=["Protocol"],
                 summary="Delete a connector in a protocol")
def delete_connector(id: str,
                     dest_process_name: str,
                     dest_process_port_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_connector_of_protocol(
            protocol_id=id,
            dest_process_name=dest_process_name,
            dest_process_port_name=dest_process_port_name
        ).to_dto()


########################## CONFIG #####################
@core_app.put("/protocol/{id}/process/{process_instance_name}/config", tags=["Protocol"],
              summary="Configure a process of a protocol")
def configure_process(id: str,
                      process_instance_name: str,
                      config_values: dict,
                      _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.configure_process(
            protocol_id=id, process_instance_name=process_instance_name, config_values=config_values).to_dto()

########################## INTERFACE / OUTERFACE #####################


@core_app.delete("/protocol/{id}/interface/{interface_name}", tags=["Protocol"],
                 summary="Delete an interface")
def delete_interface(id: str,
                     interface_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_interface_of_protocol_id(
            id, interface_name).to_dto()


@core_app.delete("/protocol/{id}/outerface/{outerface_name}", tags=["Protocol"],
                 summary="Delete an outerface")
def delete_outerface(id: str,
                     outerface_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_outerface_of_protocol_id(
            id, outerface_name).to_dto()


########################## SPECIFIC PROCESS #####################

@core_app.post("/protocol/{id}/add-source/{resource_id}/{process_name}/{input_port_name}", tags=["Protocol"],
               summary="Add a configured source link to a process' input")
def add_source_to_process_input(id: str,
                                resource_id: str,
                                process_name: str,
                                input_port_name: str,
                                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_source_to_process_input(
            protocol_id=id, resource_id=resource_id, process_name=process_name,
            input_port_name=input_port_name).to_dto()


@core_app.post("/protocol/{id}/add-source/{resource_id}", tags=["Protocol"],
               summary="Add a configured source link to a process' input")
def add_source_to_protocol(id: str,
                           resource_id: str,
                           _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_source_to_protocol_id(
            protocol_id=id, resource_id=resource_id).to_dto()


@core_app.post("/protocol/{id}/add-sink/{process_name}/{output_port_name}", tags=["Protocol"],
               summary="Add a sink link a process' output")
def add_sink_to_process_ouput(id: str,
                              process_name: str,
                              output_port_name: str,
                              _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_sink_to_process_ouput(
            protocol_id=id, process_name=process_name, output_port_name=output_port_name).to_dto()


@core_app.post("/protocol/{id}/add-viewer/{process_name}/{output_port_name}", tags=["Protocol"],
               summary="Add a viewer link a process' output")
def add_viewer_to_process_ouput(id: str,
                                process_name: str,
                                output_port_name: str,
                                _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_viewer_to_process_output(
            protocol_id=id, process_name=process_name, output_port_name=output_port_name).to_dto()


########################## LAYOUT #####################
@core_app.put("/protocol/{id}/layout", tags=["Protocol"],
              summary="Save the layout of a protocol")
def save_layout(id: str,
                layout_dict: dict,
                _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_layout(id, layout_dict)


@core_app.put("/protocol/{id}/layout/process/{process_name}", tags=["Protocol"],
              summary="Save the layout of 1 process in a protocol")
def save_process_layout(id: str,
                        process_name: str,
                        layout_dict: dict,
                        _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_process_layout(id, process_name, layout_dict)


@core_app.put("/protocol/{id}/layout/interface/{interface_name}", tags=["Protocol"],
              summary="Save the layout of 1 interface in a protocol")
def save_interface_layout(id: str,
                          interface_name: str,
                          layout_dict: dict,
                          _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_interface_layout(id, interface_name, layout_dict)


@core_app.put("/protocol/{id}/layout/outerface/{outerface_name}", tags=["Protocol"],
              summary="Save the layout of 1 outerface in a protocol")
def save_outerface_layout(id: str,
                          outerface_name: str,
                          layout_dict: dict,
                          _=Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.save_outerface_layout(id, outerface_name, layout_dict)


########################## DYNAMIC PORTS #####################
@core_app.post("/protocol/{id}/process/{process_name}/dynamic-input", tags=["Protocol"],
               summary="Add a dynamic port to a process")
def add_dynamic_input_port_to_process(id: str,
                                      process_name: str,
                                      _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_dynamic_input_port_to_process(
            id, process_name).to_dto()


@core_app.post("/protocol/{id}/process/{process_name}/dynamic-output", tags=["Protocol"],
               summary="Add a dynamic port to a process")
def add_dynamic_output_port_to_process(id: str,
                                       process_name: str,
                                       _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.add_dynamic_output_port_to_process(
            id, process_name).to_dto()


@core_app.delete("/protocol/{id}/process/{process_name}/dynamic-input/{port_name}", tags=["Protocol"],
                 summary="Delete a dynamic port of a process")
def delete_dynamic_input_port_of_process(id: str,
                                         process_name: str,
                                         port_name: str,
                                         _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_dynamic_input_port_of_process(id, process_name, port_name).to_dto()


@core_app.delete("/protocol/{id}/process/{process_name}/dynamic-output/{port_name}", tags=["Protocol"],
                 summary="Delete a dynamic port of a process")
def delete_dynamic_output_port_of_process(id: str,
                                          process_name: str,
                                          port_name: str,
                                          _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.delete_dynamic_output_port_of_process(id, process_name, port_name).to_dto()


@core_app.put("/protocol/{id}/process/{process_name}/dynamic-input/{port_name}", tags=["Protocol"],
              summary="Update a dynamic port of a process")
def update_dynamic_input_port_of_process(id: str,
                                         process_name: str,
                                         port_name: str,
                                         io_spec: IOSpecDTO,
                                         _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.update_dynamic_input_port_of_process(id, process_name, port_name, io_spec).to_dto()


@core_app.put("/protocol/{id}/process/{process_name}/dynamic-output/{port_name}", tags=["Protocol"],
              summary="Update a dynamic port of a process")
def update_dynamic_output_port_of_process(id: str,
                                          process_name: str,
                                          port_name: str,
                                          io_spec: IOSpecDTO,
                                          _=Depends(AuthService.check_user_access_token)) -> ProtocolUpdateDTO:
    with update_lock:
        return ProtocolService.update_dynamic_output_port_of_process(id, process_name, port_name, io_spec).to_dto()


########################## TEMPLATE #####################


class CreateProtocolTemplate(BaseModel):
    name: str = None
    description: Optional[dict] = None


@core_app.post("/protocol/{id}/template", tags=["Protocol"],
               summary="Create a template from a protocol")
def create_template(id: str,
                    template: CreateProtocolTemplate,
                    _=Depends(AuthService.check_user_access_token)) -> ProtocolTemplateDTO:
    return ProtocolService.create_protocol_template_from_id(id, template.name, template.description).to_dto()


@core_app.get("/protocol/{id}/template/download", tags=["Protocol"],
              summary="Download a template from a protocol")
def download_template(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    template = ProtocolService.generate_protocol_template(id)
    return ResponseHelper.create_file_response_from_str(template.to_full_dto().json(), template.name + '.json')
