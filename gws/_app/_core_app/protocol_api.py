# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/protocol/list", tags=["Protocol"], summary="Get the list of protocols")
async def get_list_of_protocols(experiment_uri: str = None, \
                                page: int = 1, \
                                number_of_items_per_page: int = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of protocols. The list is paginated.
    
    - **experiment_uri**: the uri of experiment related to the protocol (an experiment is related to one protocol).
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if no experiment_uri is not given) 
    """
    
    from gws.service.protocol_service import ProtocolService
    
    return ProtocolService.fetch_protocol_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        experiment_uri = experiment_uri,
    )

@core_app.get("/protocol-type/list", tags=["Protocol"], summary="Get the list of protocol types")
async def get_list_of_protocol_types(page: int = 1, \
                                    number_of_items_per_page: int = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of protocols. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    from gws.service.protocol_service import ProtocolService
    
    return ProtocolService.fetch_process_type_list(
        base_ptype="protocol",
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )

@core_app.get("/protocol/{uri}", tags=["Protocol"], summary="Get a protocol")
async def get_protocol(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a protocol
    
    - **uri**: the uri of the protocol
    """
    
    from gws.service.protocol_service import ProtocolService
    
    return ProtocolService.fetch_protocol(uri = uri)