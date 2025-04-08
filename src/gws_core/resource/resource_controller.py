

from typing import Dict, List, Optional

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.entity_navigator.entity_navigator_dto import ImpactResultDTO
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.resource.resource_dto import (ResourceModelDTO,
                                            ShareResourceWithSpaceRequestDTO)
from gws_core.resource.resource_transfert_service import \
    ResourceTransfertService
from gws_core.resource.view.view_dto import (CallViewResultDTO,
                                             ResourceViewMetadatalDTO)
from gws_core.share.shared_dto import ShareEntityInfoDTO, ShareLinkDTO
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.task_dto import TaskTypingDTO
from gws_core.task.transformer.transformer_service import TransformerService
from gws_core.task.transformer.transformer_type import TransformerDict

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .resource_service import ResourceService

############################# VIEW ###########################


@core_app.get("/resource/{id_}/views/{view_name}/specs", tags=["Resource"],
              summary="Get the specs for a view of a resource")
def get_view_specs_from_resource(id_: str, view_name: str,
                                 _=Depends(AuthService.check_user_access_token)) -> ResourceViewMetadatalDTO:
    return ResourceService.get_view_specs_from_resource(id_, view_name)


class CallViewParams(BaseModelDTO):
    values: dict
    save_view_config: bool


@core_app.post("/resource/{id_}/views/{view_name}", tags=["Resource"],
               summary="Call the view name for a resource")
def call_view_on_resource(id_: str,
                          view_name: str,
                          call_view_params: CallViewParams,
                          _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:

    return ResourceService.get_and_call_view_on_resource_model(
        id_, view_name, call_view_params.values,
        call_view_params.save_view_config).to_dto()


@core_app.post("/resource/{id_}/views/{view_name}/json-file", tags=["Resource"],
               summary="Get the json file of a view for a resource")
def get_view_json_file(id_: str, view_name: str,
                       call_view_params: CallViewParams,
                       _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    return ResponseHelper.create_file_response_from_object(ResourceService.get_view_json_file(
        id_, view_name, call_view_params.values,
        call_view_params.save_view_config),
        view_name + '.json')


####################################### Resource Model ###################################


@core_app.get("/resource/{id_}", tags=["Resource"], summary="Get a resource")
def get_a_resource(id_: str,
                   _=Depends(AuthService.check_user_access_token_or_streamlit_app)) -> ResourceModelDTO:
    """
    Retrieve a ResourceModel from a ResourceModel id_

    - **id_**: the id_ of the resource
    """

    return ResourceService.get_by_id_and_check(id_).to_dto()


@core_app.get("/resource/{id_}/children", tags=["Resource"], summary="Get a resource")
def get_resource_children(id_: str,
                          _=Depends(AuthService.check_user_access_token_or_streamlit_app)) -> List[ResourceModelDTO]:
    """
    Retrieve a ResourceModel children resource of a ResourceModel id_
    """

    resources = ResourceService.get_resource_children(id_)
    return [resource.to_dto() for resource in resources]


@core_app.delete("/resource/{id_}", tags=["Resource"], summary="Delete a resource")
def delete_resource(id_: str,
                    _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Delete a resource.
    """

    EntityNavigatorService.delete_resource(id_)


@core_app.get("/resource/{id_}/delete/check-impact", tags=["Resource"], summary="Check impact of resource deletion")
def check_impact_delete_resource(id_: str,
                                 _=Depends(AuthService.check_user_access_token)) -> ImpactResultDTO:

    return EntityNavigatorService.check_impact_delete_resource(id_).to_dto()


@core_app.get("/resource/search-name/{name}", tags=["Resource"],
              summary="Search resource by name")
def search_resource_by_name(
        name: str, page: Optional[int] = 1, number_of_items_per_page: Optional[int] = 20,
        _=Depends(AuthService.check_user_access_token_or_streamlit_app)) -> PageDTO[ResourceModelDTO]:
    """
    Search resource by name
    """

    return ResourceService.search_by_name(name, page, number_of_items_per_page).to_dto()


@core_app.post("/resource/advanced-search", tags=["Resource"], summary="Advanced search for resource")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token_or_streamlit_app)) -> PageDTO[ResourceModelDTO]:
    """
    Advanced search on resources
    """

    return ResourceService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.put("/resource/{id_}/name/{name}", tags=["Resource"], summary="Update the resource name")
def update_name(id_: str, name: str,
                _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:
    """
    Advanced search on resources
    """

    return ResourceService.update_name(id_, name).to_dto()


@core_app.put("/resource/{id_}/type/{resource_typing_name}", tags=["Files"], summary="Update resource type")
def update_file_type(id_: str,
                     resource_typing_name: str,
                     _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:
    return ResourceService.update_resource_type(id_, resource_typing_name).to_dto()


@core_app.put("/resource/{id_}/flagged", tags=["Resource"],
              summary="Update the flagged of a resource")
def update_flagged(id_: str,
                   body: dict,
                   _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:
    return ResourceService.update_flagged(id_, body["flagged"]).to_dto()


class UpdateFolder(BaseModelDTO):
    folder_id: Optional[str]


@core_app.put("/resource/{id_}/folder", tags=["Resource"],
              summary="Update the folder of a resource")
def update_folder(id_: str,
                  folder: UpdateFolder,
                  _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:
    return ResourceService.update_folder(id_, folder.folder_id).to_dto()

############################# TRANSFORMER ###########################


@core_app.post("/resource/{resource_model_id}/transform", tags=["Resource"],
               summary="Transform the resource")
def create_transformer_scenario(transformers: List[TransformerDict], resource_model_id: str,
                                _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:

    return TransformerService.create_and_run_transformer_scenario(
        transformers, resource_model_id).to_dto()

############################# IMPORTER ###########################


@core_app.post(
    "/resource/{resource_model_id}/import/{importer_typing_name}", tags=["Resource"],
    summary="Import the resource")
def import_resource(config: dict,
                    resource_model_id: str,
                    importer_typing_name: str,
                    _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:

    return ConverterService.call_importer(
        resource_model_id, importer_typing_name, config).to_dto()

############################# EXPORTER ###########################


@core_app.get("/resource/{resource_typing_name}/exporter", tags=["Resource"],
              summary="Get the exporter info of a resource type")
def get_exporter_config(
        resource_typing_name: str,
        _=Depends(AuthService.check_user_access_token)) -> TaskTypingDTO:

    return ConverterService.get_resource_exporter_from_name(resource_typing_name).to_full_dto()


@core_app.post("/resource/{id_}/export/{exporter_typing_name}", tags=["Resources"],
               summary="Export a resource")
def export_resource(
        id_: str,
        exporter_typing_name: str,
        params: dict,
        _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:
    """
    Export a resource.
    """
    return ConverterService.call_exporter(
        resource_model_id=id_, exporter_typing_name=exporter_typing_name, params=params).to_dto()

############################# RESOURCE TYPE ###########################


@core_app.get("/resource-type/{resource_typing_name}/views", tags=["Resource type"],
              summary="Get the list of view for a resource type")
def get_resource_type_views(resource_typing_name: str,
                            _=Depends(AuthService.check_user_access_token)) -> List[ResourceViewMetadatalDTO]:
    view_metadatas = ResourceService.get_views_of_resource(resource_typing_name)
    return [view_metadata.to_dto() for view_metadata in view_metadatas]


@core_app.get("/resource-type/{resource_type}/views/{view_name}/specs", tags=["Resource type"],
              summary="Get the specs for a view of a resource type")
def get_view_specs_from_type(resource_type: str, view_name: str,
                             _=Depends(AuthService.check_user_access_token)) -> ResourceViewMetadatalDTO:
    return ResourceService.get_view_specs_from_type(resource_type, view_name)


############################# SHARED RESOURCE ###########################


@core_app.get("/resource/{id_}/shared-origin", tags=["Resource"],
              summary="Get origin of this imported resource", response_model=None)
def get_shared_resource_origin_info(id_: str,
                                    _=Depends(AuthService.check_user_access_token)) -> ShareEntityInfoDTO:
    return ResourceService.get_shared_resource_origin_info(id_).to_dto()


################################ RESOURCE ################################


@core_app.post("/resource/import-from-link", tags=["Share"],
               summary="Download a resource from an external link")
def import_resource_from_link(values: ConfigParamsDict,
                              _=Depends(AuthService.check_user_access_token)) -> ResourceModelDTO:
    return ResourceTransfertService.import_resource_from_link_sync(values).to_dto()


@core_app.get("/resource/import-from-link/config-specs", tags=["Share"],
              summary="Get config specs for importing a resource from a link")
def get_import_resource_config_specs(_=Depends(AuthService.check_user_access_token)) -> Dict[str, ParamSpecDTO]:
    return ResourceTransfertService.get_import_from_link_config_specs()


@core_app.post("/resource/{resource_id}/export-to-lab", tags=["Share"],
               summary="Export a resource to a lab")
def export_resource_to_lab(resource_id: str, values: ConfigParamsDict,
                           _=Depends(AuthService.check_user_access_token)) -> None:
    ResourceTransfertService.export_resource_to_lab(resource_id, values)


@core_app.get("/resource/export-to-lab/config-specs", tags=["Share"],
              summary="Get config specs for exporting a resource to a lab")
def get_export_resource_to_lab_config_specs(_=Depends(AuthService.check_user_access_token)) -> Dict[str, ParamSpecDTO]:
    return ResourceTransfertService.get_export_resource_to_lab_config_specs()


@core_app.post("/resource/{resource_id}/share-with-space", tags=["Share"],
               summary="Share a resource with the space")
def share_resource_with_space(resource_id: str, request_dto: ShareResourceWithSpaceRequestDTO,
                              _=Depends(AuthService.check_user_access_token)) -> ShareLinkDTO:
    return ResourceTransfertService.share_resource_with_space(resource_id, request_dto).to_dto()
