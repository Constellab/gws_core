# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from fastapi import Depends
from gws_core.core.dto.typed_tree_dto import TypedTree
from gws_core.protocol.protocol_type import ProtocolType

from ..core_app import core_app
from ..process.process_service import ProcessService
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .protocol_service import ProtocolService


@core_app.get("/protocol/{uri}/progress-bar", tags=["Protocol"], summary="Get the progress bar of a protocol")
async def get_the_progress_bar_of_a_protocol(uri: str,
                                             _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a process

    - **uri**: the uri of the process
    """

    pbar = ProcessService.fetch_process_progress_bar(uri=uri)
    return pbar.to_json()


@core_app.get("/protocol/{uri}", tags=["Protocol"], summary="Get a protocol")
async def get_a_protocol(uri: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a protocol

    - **uri**: the uri of the protocol
    """

    proto = ProtocolService.get_protocol_by_uri(uri=uri)
    return proto.to_json()


@core_app.get("/protocol", tags=["Protocol"], summary="Get the list of protocols")
async def get_the_list_of_protocols(page: Optional[int] = 1,
                                    number_of_items_per_page: Optional[int] = 20,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a list of protocols. The list is paginated.

    - **type**: the type of the processes to fetch
    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search. If this parameter is given then the parameter `experiment_uri` is ignored.
    - **experiment_uri**: the uri of the experiment related to the processes. This parameter is ignored if `search_text` is given.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50)
    """

    return ProtocolService.fetch_protocol_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
        as_json=True
    )

############################# PROTOCOL TYPE ###########################


@core_app.get("/protocol-type/{uri}", tags=["Protocol"], summary="Get a protocol type detail")
async def get_protocol_type(uri: str,
                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a protocol

    - **uri**: the uri of the protocol
    """

    proto: ProtocolType = ProtocolService.get_protocol_type(uri=uri)
    return proto.to_json(deep=True)


@core_app.get("/protocol-type", tags=["Protocol"], summary="Get the list of protocol types")
async def get_the_list_of_protocol_types(page: Optional[int] = 1,
                                         number_of_items_per_page: Optional[int] = 20,
                                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a list of protocols. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ProtocolService.fetch_protocol_type_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


@core_app.get("/protocol-type/typedTree", tags=["Protocol"],
              summary="Get the list of protocol types grouped by python module")
async def get_the_list_of_process_grouped(_: UserData = Depends(AuthService.check_user_access_token)) -> List[TypedTree]:
    """
    Retrieve all the process types in TypedTree
    """

    return ProtocolService.fetch_process_type_tree()
