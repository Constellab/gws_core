# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.dto.user_dto import UserData
from fastapi import Depends
from typing import Optional

from ._auth_user import check_user_access_token
from .core_app import core_app
from gws.service.protocol_service import ProtocolService
from gws.service.process_service import ProcessService


@core_app.get("/protocol-type", tags=["Protocol"], summary="Get the list of protocol types")
async def get_the_list_of_protocol_types(page: Optional[int] = 1, \
                                         number_of_items_per_page: Optional[int] = 20, \
                                         _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a list of protocols. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ProtocolService.fetch_protocol_type_list(
        page = page,
        number_of_items_per_page = number_of_items_per_page,
        as_json = True
    )

@core_app.get("/protocol/{uri}/{type}/progress-bar", tags=["Protocol"], summary="Get the progress bar of a protocol")
async def get_the_progress_bar_of_a_protocol(uri: str, \
                      type: Optional[str] = "gws.model.Process", \
                       _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a process
    
    - **uri**: the uri of the process
    """
       
    pbar = ProcessService.fetch_process_progress_bar(uri=uri, type=type)
    return pbar.to_json()

@core_app.get("/protocol/{uri}/{type}", tags=["Protocol"], summary="Get a protocol")
async def get_a_protocol(uri: str, \
                         type: Optional[str] = "gws.model.Protocol", \
                         _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a protocol
    
    - **uri**: the uri of the protocol
    """
    
    proto = ProtocolService.fetch_protocol(uri=uri, type=type)
    return proto.to_json()


@core_app.get("/protocol", tags=["Protocol"], summary="Get the list of protocols")
async def get_the_list_of_protocols(type: Optional[str] = "gws.model.Protocol", \
                                    search_text: Optional[str]="", \
                                    experiment_uri: Optional[str] = None, \
                                    page: Optional[int] = 1, \
                                    number_of_items_per_page: Optional[int] = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a list of protocols. The list is paginated.
    
    - **type**: the type of the processes to fetch
    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search. If this parameter is given then the parameter `experiment_uri` is ignored.
    - **experiment_uri**: the uri of the experiment related to the processes. This parameter is ignored if `search_text` is given.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """
    
    return ProtocolService.fetch_protocol_list(
        type=type,
        search_text=search_text,
        experiment_uri = experiment_uri,
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        as_json = True
    )