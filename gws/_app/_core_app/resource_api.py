# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from typing import Optional

from ._auth_user import UserData, check_user_access_token
from .core_app import core_app
from gws.service.resource_service import ResourceService

@core_app.get("/resource-type", tags=["Resource"], summary="Get the list of resource types")
async def get_the_list_of_resource_types(page: Optional[int] = 1, \
                                     number_of_items_per_page: Optional[int] = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of resources. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    from gws.service.resource_service import ResourceService
    
    return ResourceService.fetch_resource_type_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page, 
        as_json = True
    )

@core_app.get("/resource/{type}/{uri}", tags=["Resource"], summary="Get a resource")
async def get_a_resource(type: str, \
                         uri: str, \
                         _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a resource
    
    - **uri**: the uri of the protocol
    """
    
    r = ResourceService.fetch_resource(type=type, uri=uri)
    return r.to_json()

@core_app.get("/resource/{type}", tags=["Resource"], summary="Get the list of resources")
async def get_the_list_of_resources(type: Optional[str] = "gws.model.Resource", \
                                search_text: Optional[str]="", \
                                experiment_uri: Optional[str] = None, \
                                page: Optional[int] = 1, \
                                number_of_items_per_page: Optional[int] = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve the list of resources. The list is paginated.

     - **type**: the type of the processes to fetch
    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search. If this parameter is given then the parameter `experiment_uri` is ignored.
    - **experiment_uri**: the uri of the experiment related to the processes. This parameter is ignored if `search_text` is given.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    
    
    return ResourceService.fetch_resource_list(
        type=type,
        search_text=search_text,
        experiment_uri = experiment_uri,
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        as_json = True
    )