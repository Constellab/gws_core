# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/resource/list", tags=["Resource"], summary="Get the list of resources")
async def get_list_of_resources(resource_type="resource", \
                                experiment_uri: str = None, \
                                page: int = 1, \
                                number_of_items_per_page: int = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve the list of resources. The list is paginated.

    - **resource_type**: the type of resources to load. Since use resource may be save in different table, it my be needed to specifiy the type of the resources to retrieve. The default is **resource** to search in the base resource table.
    - **experiment_uri**: the uri of the exepriment in which the resource was generated
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    from gws.service.resource_service import ResourceService
    
    return ResourceService.fetch_resource_list(
        resource_type=resource_type,
        page = page, 
        number_of_items_per_page = number_of_items_per_page, 
        experiment_uri = experiment_uri
    )

@core_app.get("/resource-type/list", tags=["Resource"], summary="Get the list of resource types")
async def get_list_of_resource_types(page: int = 1, \
                                    number_of_items_per_page: int = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of resources. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    from gws.service.resource_service import ResourceService
    
    return ResourceService.fetch_resource_type_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )