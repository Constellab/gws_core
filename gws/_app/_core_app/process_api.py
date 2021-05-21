# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from typing import Optional

from ._auth_user import UserData, check_user_access_token
from .core_app import core_app
from gws.service.process_service import ProcessService

@core_app.get("/process-type", tags=["Process"], summary="Get the list of process types")
async def get_the_list_of_process_types(page: Optional[int] = 1, \
                                    number_of_items_per_page: Optional[int] = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a list of processes. The list is paginated.
    
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
        
    return ProcessService.fetch_process_type_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        as_json = True
    )

@core_app.get("/process/{type}/{uri}/progress-bar", tags=["Process"], summary="Get the progress bar of a process")
async def get_the_progress_bar_of_a_process(type: str, \
                                            uri: str, \
                                            _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a process
    
    - **uri**: the uri of the process (Default is `gws.model.Process`)
    """
       
    bar = ProcessService.fetch_process_progress_bar(uri=uri, type=type)
    return bar.to_json()

@core_app.get("/process/{type}/{uri}", tags=["Process"], summary="Get a process")
async def get_a_process(type: str, \
                        uri: str, \
                        _: UserData = Depends(check_user_access_token)) -> dict:
    """
    Retrieve a process
    
    - **type**: the type of the process (Default is `gws.model.Process`)
    - **uri**: the uri of the process
    """
       
    proc = ProcessService.fetch_process(type=type, uri=uri)
    return proc.to_json()

@core_app.get("/process/{type}", tags=["Process"], summary="Get the list of processes")
async def get_the_list_of_processes(type: str, \
                                search_text: Optional[str]="", \
                                experiment_uri: Optional[str] = None, \
                                page: Optional[int] = 1, \
                                number_of_items_per_page: Optional[int] = 20, \
                                _: UserData = Depends(check_user_access_token)) -> dict:
    
    """
    Retrieve a list of processes. The list is paginated.

    - **type**: the type of the processes to fetch (Default is `gws.model.Process`)
    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search. If this parameter is given then the parameter `experiment_uri` is ignored.
    - **experiment_uri**: the uri of the experiment related to the processes. This parameter is ignored if `search_text` is given.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page. 
    """

    return ProcessService.fetch_process_list(
        type=type,
        search_text=search_text,
        experiment_uri = experiment_uri,
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        as_json = True
    )
