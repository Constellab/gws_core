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


@core_app.get("/protocol/{uri}", tags=["Protocol"], summary="Get a protocol")
async def get_a_protocol(uri: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a protocol

    - **uri**: the uri of the protocol
    """

    proto = ProtocolService.get_protocol_by_uri(uri=uri)
    return proto.to_json(deep=True)


@core_app.get("/protocol", tags=["Protocol"], summary="Get the list of protocols")
async def get_the_list_of_protocols(page: Optional[int] = 1,
                                    number_of_items_per_page: Optional[int] = 20,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a list of protocols. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50)
    """

    return ProtocolService.fetch_protocol_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


@core_app.post("/protocol/{uri}/add-process/{process_typing_name}", tags=["Protocol"],
               summary="Add a process to a protocol")
async def add_process(uri: str,
                      process_typing_name: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Add a process to a protocol
    """

    return ProtocolService.add_process_to_protocol(
        protocol_uri=uri,
        process_typing_name=process_typing_name
    ).to_json(deep=True)

############################# PROTOCOL TYPE ###########################


@core_app.get("/protocol-type", tags=["Protocol"], summary="Get the list of protocol types")
async def get_the_list_of_protocol_types(page: Optional[int] = 1,
                                         number_of_items_per_page: Optional[int] = 20,
                                         _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve a list of protocols. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ProtocolService.fetch_protocol_type_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


@core_app.get("/protocol-type/tree", tags=["Protocol"],
              summary="Get the list of protocol types grouped by python module")
async def get_the_list_of_process_grouped(_: UserData = Depends(AuthService.check_user_access_token)) -> List[TypedTree]:
    """
    Retrieve all the process types in TypedTree
    """

    return ProtocolService.fetch_protocol_type_tree()


@core_app.get("/protocol-type/{uri}", tags=["Protocol"], summary="Get a protocol type detail")
async def get_protocol_type(uri: str,
                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a protocol type

    - **uri**: the uri of the protocol type
    """

    return ProtocolService.get_protocol_type(uri=uri).to_json(deep=True)
