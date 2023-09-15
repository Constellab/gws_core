# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional

from fastapi import Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from gws_core.core.classes.search_builder import SearchParams
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.view_types import CallViewParams
from gws_core.share.shared_resource import SharedResource
from gws_core.tag.tag import Tag
from gws_core.tag.tag_service import TagService
from gws_core.task.action.action_service import ActionService
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.transformer.transformer_service import TransformerService
from gws_core.task.transformer.transformer_type import TransformerDict

from ..core.classes.jsonable import ListJsonable
from ..core_app import core_app
from ..user.auth_service import AuthService
from .resource_service import ResourceService

############################# VIEW ###########################


@core_app.get("/resource/{id}/views/{view_name}/specs", tags=["Resource"],
              summary="Get the specs for a view of a resource")
def get_view_specs_from_resource(id: str, view_name: str,
                                 _=Depends(AuthService.check_user_access_token)) -> dict:
    return ResourceService.get_view_specs_from_resource(id, view_name)


@core_app.post("/resource/{id}/views/{view_name}", tags=["Resource"],
               summary="Call the view name for a resource")
def call_view_on_resource(id: str,
                          view_name: str,
                          call_view_params: CallViewParams,
                          _=Depends(AuthService.check_user_access_token)):

    return ResourceService.get_and_call_view_on_resource_model(
        id, view_name, call_view_params["values"],
        call_view_params["save_view_config"]).to_json()


####################################### Resource Model ###################################


@core_app.get("/resource/{id}", tags=["Resource"], summary="Get a resource")
def get_a_resource(id: str,
                   _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a ResourceModel from a ResourceModel ID

    - **id**: the id of the resource
    """

    return ResourceService.get_resource_by_id(id=id).to_json(
        deep=True)


@core_app.get("/resource/{id}/children", tags=["Resource"], summary="Get a resource")
def get_resource_children(id: str,
                          _=Depends(AuthService.check_user_access_token)) -> list:
    """
    Retrieve a ResourceModel children resource of a ResourceModel ID
    """

    return ListJsonable(ResourceService.get_resource_children(id=id)).to_json()


@core_app.delete("/resource/{id}", tags=["Resource"], summary="Delete a resource")
def delete_file(id: str,
                _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Delete a resource.
    """

    return ResourceService.delete(id)


@core_app.post("/resource/advanced-search", tags=["Resource"], summary="Advanced search for resource")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search on resources
    """

    return ResourceService.search(search_dict, page, number_of_items_per_page).to_json()


@core_app.put("/resource/{id}/name/{name}", tags=["Resource"], summary="Update the resource name")
def update_name(id: str, name: str,
                _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Advanced search on resources
    """

    return ResourceService.update_name(id, name).to_json(deep=True)


@core_app.put("/resource/{id}/type/{resource_typing_name}", tags=["Files"], summary="Update resource type")
def update_file_type(id: str,
                     resource_typing_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> Dict:
    return ResourceService.update_resource_type(id, resource_typing_name).to_json()


@core_app.put("/resource/{id}/flagged", tags=["Resource"],
              summary="Update the flagged of a resource")
def update_flagged(id: str,
                   body: dict,
                   _=Depends(AuthService.check_user_access_token)) -> Dict:
    return ResourceService.update_flagged(id, body["flagged"]).to_json(deep=True)


class UpdateProject(BaseModel):
    project_id: Optional[str]


@core_app.put("/resource/{id}/project", tags=["Resource"],
              summary="Update the project of a resource")
def update_project(id: str,
                   project: UpdateProject,
                   _=Depends(AuthService.check_user_access_token)) -> Dict:
    return ResourceService.update_project(id, project.project_id).to_json(deep=True)
############################# TAGS ###########################


@core_app.put("/resource/{id}/tags", tags=["Resource"], summary="Update resource tags")
def save_tags(id: str,
              tags: List[Tag],
              _=Depends(AuthService.check_user_access_token)) -> list:
    return ListJsonable(TagService.save_tags_to_entity(ResourceModel, id, tags)).to_json()


############################# TRANSFORMER ###########################


@core_app.post("/resource/{resource_model_id}/transform", tags=["Resource"],
               summary="Transform the resource")
def create_transformer_experiment(transformers: List[TransformerDict], resource_model_id: str,
                                  _=Depends(AuthService.check_user_access_token)) -> dict:

    resource_model: ResourceModel = TransformerService.create_and_run_transformer_experiment(
        transformers, resource_model_id)
    return resource_model.to_json()

############################# IMPORTER ###########################


@core_app.post(
    "/resource/{resource_model_id}/import/{importer_typing_name}", tags=["Resource"],
    summary="Import the resource")
def import_resource(config: dict,
                    resource_model_id: str,
                    importer_typing_name: str,
                    _=Depends(AuthService.check_user_access_token)) -> dict:

    resource_model: ResourceModel = ConverterService.call_importer(
        resource_model_id, importer_typing_name, config)
    return resource_model.to_json()

############################# EXPORTER ###########################


@core_app.get("/resource/{resource_typing_name}/exporter", tags=["Resource"],
              summary="Get the exporter info of a resource type")
def get_exporter_config(
        resource_typing_name: str,
        _=Depends(AuthService.check_user_access_token)) -> dict:

    return ConverterService.get_resource_exporter_from_name(resource_typing_name).to_json(deep=True)


@core_app.get(
    "/resource/{id}/download/{exporter_typing_name}", tags=["Resources"],
    summary="Download a resource")
def download_a_resource(
        exporter_typing_name: str,
        request: Request,
        id=str,
        _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    """
    Download a file. The access is made with a unique  code generated with get_download_file_url
    """
    return ResourceService.download_resource(
        id=id, exporter_typing_name=exporter_typing_name, params=request.query_params)

############################# RESOURCE TYPE ###########################


@core_app.get("/resource-type/{resource_typing_name}/views", tags=["Resource type"],
              summary="Get the list of view for a resource type")
def get_resource_type_views(resource_typing_name: str,
                            _=Depends(AuthService.check_user_access_token)) -> list:
    return ListJsonable(ResourceService.get_views_of_resource(resource_typing_name)).to_json()


@core_app.get("/resource-type/{resource_type}/views/{view_name}/specs", tags=["Resource type"],
              summary="Get the specs for a view of a resource type")
def get_view_specs_from_type(resource_type: str, view_name: str,
                             _=Depends(AuthService.check_user_access_token)) -> dict:
    return ResourceService.get_view_specs_from_type(resource_type, view_name)


############################### ACTIONS ##############################

@core_app.post("/resource/{id}/action/add/{action_typing_name}", tags=["Resource"],
               summary="Add an action to a resource")
def add_action_to_resource(id: str, action_typing_name: str,
                           action_params: dict,
                           _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Add an action to a resource.
    """
    return ActionService.execute_action(id, action_typing_name, action_params).to_json()


############################# SHARED RESOURCE ###########################


@core_app.get("/resource/{id}/shared-origin", tags=["Resource"],
              summary="Get origin of this imported resource", response_model=None)
def get_shared_resource_origin_info(id: str,
                                    _=Depends(AuthService.check_user_access_token)) -> dict:
    return ResourceService.get_shared_resource_origin_info(id).to_json()


################################ RESOURCE ################################

class ImportDto(BaseModel):
    url: str
    uncompress_option: str


@core_app.post("/resource/upload-from-link", tags=["Share"], summary="Download a resource", response_model=None)
def upload_resource_from_link(import_dto: ImportDto,
                              _=Depends(AuthService.check_user_access_token)) -> dict:
    return ResourceService.upload_resource_from_link(import_dto.url, import_dto.uncompress_option).to_json()
