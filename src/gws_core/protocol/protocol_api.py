# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends
from gws_core.config.config_types import ConfigParamsDict
from gws_core.protocol.protocol_action import AddConnectorDTO
from pydantic import BaseModel

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .protocol_service import ProtocolService


@core_app.get("/protocol/{id}", tags=["Protocol"], summary="Get a protocol")
async def get_a_protocol(id: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a protocol

    - **id**: the id of the protocol
    """

    proto = ProtocolService.get_protocol_by_id(id=id)
    return proto.to_json(deep=True)


@core_app.post("/protocol/{id}/add-process/{process_typing_name}", tags=["Protocol"],
               summary="Add a process to a protocol")
async def add_process(id: str,
                      process_typing_name: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Add a process to a protocol
    """

    return ProtocolService.add_process_to_protocol_id(
        protocol_id=id,
        process_typing_name=process_typing_name
    ).to_json(deep=True)


@core_app.delete("/protocol/{id}/process/{process_instance_name}", tags=["Protocol"],
                 summary="Delete a process of a protocol")
async def delete_process(id: str,
                         process_instance_name: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.delete_process_of_protocol(
        protocol_id=id,
        process_instance_name=process_instance_name
    )

########################## CONNECTORS #####################


@core_app.post("/protocol/{id}/connector", tags=["Protocol"],
               summary="Add a connector between 2 process of a protocol")
async def add_connector(id: str,
                        add_connector: AddConnectorDTO,
                        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    return ProtocolService.add_connector_to_protocol_id(
        protocol_id=id,
        output_process_name=add_connector.output_process_name,
        out_port_name=add_connector.out_port_name,
        input_process_name=add_connector.input_process_name,
        in_port_name=add_connector.in_port_name,
    ).to_json(deep=True)


@core_app.delete("/protocol/{id}/connector/{dest_process_name}/{dest_process_port_name}", tags=["Protocol"],
                 summary="Delete a connector in a protocol")
async def delete_connector(id: str,
                           dest_process_name: str,
                           dest_process_port_name: str,
                           _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    ProtocolService.delete_connector_of_protocol(
        protocol_id=id,
        dest_process_name=dest_process_name,
        dest_process_port_name=dest_process_port_name
    )


########################## CONFIG #####################
@core_app.put("/protocol/{id}/process/{process_instance_name}", tags=["Protocol"],
              summary="Configure a process of a protocol")
async def configure_process(id: str,
                            process_instance_name: str,
                            config_values: ConfigParamsDict,
                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    return ProtocolService.configure_process(
        protocol_id=id, process_instance_name=process_instance_name, config_values=config_values).to_json(
        deep=True)


########################## SPECIFIC PROCESS #####################

@core_app.post("/protocol/{id}/add-source/{process_name}/{input_port_name}/{resource_id}", tags=["Protocol"],
               summary="Add a configured source link to a process' input")
async def add_source_to_process_input(id: str,
                                      process_name: str,
                                      input_port_name: str,
                                      resource_id: str,
                                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return ProtocolService.add_source_to_process_input(
        protocol_id=id, process_name=process_name, input_port_name=input_port_name, resource_id=resource_id
    ).to_json()


@core_app.post("/protocol/{id}/add-sink/{process_name}/{output_port_name}", tags=["Protocol"],
               summary="Add a sink link a process' output")
async def add_sink_to_process_ouput(id: str,
                                    process_name: str,
                                    output_port_name: str,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return ProtocolService.add_sink_to_process_ouput(
        protocol_id=id, process_name=process_name, output_port_name=output_port_name).to_json()
