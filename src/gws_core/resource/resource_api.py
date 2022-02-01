# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Optional

from fastapi import Depends, Request
from fastapi.responses import FileResponse
from gws_core.core.classes.search_builder import SearchDict
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.transformer.transformer_service import TransformerService
from gws_core.task.transformer.transformer_type import TransformerDict
from typing_extensions import TypedDict

from ..core.classes.jsonable import DictJsonable, ListJsonable
from ..core.classes.paginator import PaginatorDict
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .resource_service import ResourceService

############################# VIEW ###########################


@core_app.get("/resource/{id}/views", tags=["Resource"],
              summary="Get the list of view for a resource type")
async def get_resource_type_views(id: str) -> list:
    return ListJsonable(ResourceService.get_views_of_resource(id)).to_json()


@core_app.get("/resource/{id}/views/{view_name}/specs", tags=["Resource"],
              summary="Get the specs for a view of a resource")
async def get_view_specs(id: str, view_name: str) -> list:
    return DictJsonable(ResourceService.get_view_specs(id, view_name)).to_json()


class ViewConfig(TypedDict):
    values: Dict[str, Any]
    transformers: List[TransformerDict]


@core_app.post("/resource/{id}/views/{view_name}", tags=["Resource"],
               summary="Call the view name for a resource")
async def call_view_on_resource(id: str,
                                view_name: str,
                                view_config: ViewConfig) -> Any:
    return await ResourceService.call_view_on_resource_type(id, view_name, view_config["values"], view_config["transformers"])


@core_app.post("/resource/{id}/default-view", tags=["Resource"],
               summary="Call the default view for a resource")
async def call_default_view_on_resource(id: str) -> Any:
    return await ResourceService.call_default_view_on_resource(id)


####################################### Resource Model ###################################

@core_app.get("/resource/by-type/{resource_typing_name}", tags=["Resource"], summary="Get the list of resources")
async def get_the_list_of_resources(resource_typing_name: Optional[str] = None,
                                    page: Optional[int] = 1,
                                    number_of_items_per_page: Optional[int] = 20,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve the list of resources from resource type. The list is paginated.

    - **resource_typing_name**: typing name of the resource to fetch
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ResourceService.get_resources_of_type(
        resource_typing_name=resource_typing_name,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


@core_app.get("/resource/{id}", tags=["Resource"], summary="Get a resource")
async def get_a_resource(id: str,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a ResourceModel from a ResourceModel ID

    - **id**: the id of the protocol
    """

    return ResourceService.get_resource_by_id(id=id).to_json(
        deep=True)


@core_app.delete("/resource/{id}", tags=["Resource"], summary="Delete a resource")
async def delete_file(id: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    """
    Delete a resource.
    """

    return ResourceService.delete(id)


@core_app.post("/resource/advanced-search", tags=["Resource"], summary="Advanced search for resource")
async def advanced_search(search_dict: SearchDict,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    """
    Advanced search on resources
    """

    return ResourceService.search(search_dict, page, number_of_items_per_page).to_json()


@core_app.put("/resource/{id}/name/{name}", tags=["Resource"], summary="Update the resource name")
async def update_name(id: str, name: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    """
    Advanced search on resources
    """

    return ResourceService.update_name(id, name).to_json(deep=True)


@core_app.put("/resource/{id}/type/{resource_typing_name}", tags=["Files"], summary="Update resource type")
def update_file_type(id: str,
                     resource_typing_name: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ResourceService.update_resource_type(id, resource_typing_name).to_json()

############################# IMPORTER ###########################


@core_app.post("/resource/{resource_model_id}/transform", tags=["Resource"],
               summary="Transform the resource")
async def create_transformer_experiment(transformers: List[TransformerDict], resource_model_id: str,
                                        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    resource_model: ResourceModel = await TransformerService.create_and_run_transformer_experiment(transformers, resource_model_id)
    return resource_model.to_json()

############################# IMPORTER ###########################


@core_app.get("/resource-type/{resource_typing_name}/importer", tags=["Resource"],
              summary="Get specs to import the resource")
async def get_import_specs(resource_typing_name: str,
                           _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    return ListJsonable(ConverterService.get_resource_importers(resource_typing_name)).to_json()


@core_app.post(
    "/resource/{resource_model_id}/import/{importer_typing_name}", tags=["Resource"],
    summary="Import the resource")
async def import_resource(config: dict,
                          resource_model_id: str,
                          importer_typing_name: str,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    resource_model: ResourceModel = await ConverterService.call_importer(resource_model_id, importer_typing_name, config)
    return resource_model.to_json()

############################# EXPORTER ###########################


@core_app.get("/resource/{resource_typing_name}/exporter", tags=["Resource"],
              summary="Get the exporter info of a resource type")
async def get_exporter_config(
        resource_typing_name: str,
        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    return ConverterService.get_resource_exporter_from_name(resource_typing_name).to_json(deep=True)


@core_app.get("/resource/{id}/{exporter_typing_name}/get-download-url", tags=["Resources"],
              summary="Get a unique url to download the resource")
def get_download_resource_url(
        id: str,
        exporter_typing_name: str,
        _: UserData = Depends(AuthService.check_user_access_token)) -> str:
    """
    Generate a unique url to download the file
    """
    return f'resource/download/{ResourceService.generate_download_resource_url(id=id)}/{exporter_typing_name}'


@core_app.get(
    "/resource/download/{unique_code}/{exporter_typing_name}", tags=["Resources"],
    summary="Download a resource")
def download_a_resource(
        exporter_typing_name: str,
        request: Request,
        id=Depends(AuthService.check_unique_code)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    return ResourceService.download_resource(
        id=id, exporter_typing_name=exporter_typing_name, params=request.query_params)

############################# RESOURCE TYPE ###########################


@core_app.get("/resource-type", tags=["Resource"], summary="Get the list of resource types")
async def get_the_list_of_resource_types(_: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a the complete list of resources types. The list is not paginated.
    """
    return ListJsonable(ResourceService.fetch_resource_type_list()).to_json()
