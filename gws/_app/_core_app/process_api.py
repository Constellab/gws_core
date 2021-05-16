# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/process/list", tags=["Process"], summary="Get the list of processes")
async def get_list_of_process(experiment_uri: str = None, \
                              page: int = 1, \
                              number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page. 
    """
    
    from gws.service.process_service import ProcessService
    
    return ProcessService.fetch_process_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        experiment_uri = experiment_uri
    )

@core_app.get("/process-type/list", tags=["Process"], summary="Get the list of process types")
async def get_list_of_process_types(page: int = 1, \
                                    number_of_items_per_page: int = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    from gws.service.process_service import ProcessService
    
    return ProcessService.fetch_process_type_list(
        base_ptype="process",
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )

@core_app.get("/process/{uri}", tags=["Process"], summary="Get a process")
async def get_process(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a process
    
    - **uri**: the uri of the process
    """
    
    from gws.service.process_service import ProcessService
    
    return ProcessService.fetch_process(uri = uri)