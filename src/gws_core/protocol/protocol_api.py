# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from fastapi import Depends

from ..core.classes.paginator import PaginatorDict
from ..core.dto.typed_tree_dto import TypedTree
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
