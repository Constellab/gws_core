# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from re import S
from typing import Any, Dict, List, Optional

from fastapi import Depends
from gws_core.core.classes.paginator import PaginatorDict
from gws_core.resource.view_decorator import ResourceViewMetaData

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .resource_service import ResourceService


@core_app.get("/resource/{resource_model_typing_name}/{uri}", tags=["Resource"], summary="Get a resource")
async def get_a_resource(resource_model_typing_name: str,
                         uri: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a ResourceModel from a ResourceModel type and URI

    - **uri**: the uri of the protocol
    """

    return ResourceService.fetch_resource(
        resource_model_typing_name=resource_model_typing_name, uri=uri).to_json(
        deep=True)


@core_app.get("/resource/{resource_typing_name}", tags=["Resource"], summary="Get the list of resources")
async def get_the_list_of_resources(resource_typing_name: Optional[str] = None,
                                    experiment_uri: Optional[str] = None,
                                    page: Optional[int] = 1,
                                    number_of_items_per_page: Optional[int] = 20,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve the list of resources from resource type. The list is paginated.

     - **type**: the type of the processes to fetch
    - **experiment_uri**: the uri of the experiment related to the processes. This parameter is ignored if `search_text` is given.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ResourceService.fetch_resource_list(
        resource_typing_name=resource_typing_name,
        experiment_uri=experiment_uri,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()

############################# RESOURCE TYPE ###########################


@core_app.get("/resource-type", tags=["Resource"], summary="Get the list of resource types")
async def get_the_list_of_resource_types(page: Optional[int] = 1,
                                         number_of_items_per_page: Optional[int] = 20,
                                         _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve a list of resources. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    return ResourceService.fetch_resource_type_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


############################# VIEW ###########################

@core_app.get("/resource/{resource_typing_name}/views", tags=["Resource"],
              summary="Get the list of view for a resource type")
async def get_resource_type_views(resource_typing_name: str) -> List[ResourceViewMetaData]:
    return ResourceService.get_views_of_resource(resource_typing_name)


@core_app.post("/resource/{resource_typing_name}/{uri}/views{view_name}", tags=["Resource"],
               summary="Call the view name for a resource")
async def call_view_on_resource(resource_typing_name: str,
                                uri: str,
                                view_name: str,
                                config: Dict[str, Any]) -> Any:
    return ResourceService.call_view_on_resource_type(resource_typing_name, uri, view_name, config)
