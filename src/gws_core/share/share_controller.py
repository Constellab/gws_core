

from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core.model.model_dto import PageDTO
from gws_core.core_controller import core_app
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.resource_controller import CallViewParams
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.share.share_token_auth import ShareTokenAuth
from gws_core.share.shared_dto import (ShareEntityInfoDTO, ShareLinkEntityType,
                                       ShareResourceInfoReponseDTO,
                                       ShareResourceZippedResponseDTO,
                                       ShareScenarioInfoReponseDTO)
from gws_core.user.auth_context import AuthContextShareLink
from gws_core.user.authorization_service import AuthorizationService

from .share_service import ShareService


# Open to mark the resource as downloaded by another lab
@core_app.post("/share/{entity_type}/mark-as-shared/{token}", tags=["Share"],
               summary="Mark the resource as downloaded by another lab")
def mark_entity_as_shared(
        entity_type: ShareLinkEntityType, receiver_lab: ExternalLabWithUserInfo,
        auth_context: AuthContextShareLink = Depends(ShareTokenAuth.get_and_check_share_link_token_from_url)) -> None:
    ShareService.mark_entity_as_shared(entity_type, auth_context.get_share_link(), receiver_lab)


@core_app.get("/share/{entity_type}/{entity_id}/shared-to", tags=["Share"],
              summary="Get info about which lab this object was shared to", response_model=None)
def get_shared_to_list(entity_type: ShareLinkEntityType,
                       entity_id: str,
                       _=Depends(AuthorizationService.check_user_access_token)) -> PageDTO[ShareEntityInfoDTO]:
    return ShareService.get_shared_to_list(entity_type, entity_id).to_dto()

#################################### ROUTE WITH TOKEN IN URL ####################################
################################ RESOURCE ################################
# Open route to get info about a shared entity
# Same as above


@core_app.get("/share/resource/{token}", tags=["Share"], summary="Download a resource")
def get_share_resource_info(
        auth_context: AuthContextShareLink = Depends(ShareTokenAuth.get_and_check_share_link_token_from_url)) -> ShareResourceInfoReponseDTO:
    return ShareService.get_resource_entity_object_info(auth_context.get_share_link())


# Open zip the shared entity
@core_app.post("/share/resource/{token}/zip", tags=["Share"], summary="Zip the shared entity")
def zip_resource(auth_context: AuthContextShareLink = Depends(ShareTokenAuth.get_and_check_share_link_token_from_url)) -> ShareResourceZippedResponseDTO:
    return ShareService.zip_shared_resource(auth_context.get_share_link())


# Open route to download a resource
@core_app.get("/share/resource/{token}/download", tags=["Share"], summary="Download a zipped entity")
def download_resource(auth_context: AuthContextShareLink = Depends(
        ShareTokenAuth.get_and_check_share_link_token_from_url)) -> FileResponse:
    file_path = ShareService.download_zipped_resource(auth_context.get_share_link())
    return FileHelper.create_file_response(file_path)


################################ SCENARIO ################################

# Route to get scenario info
@core_app.get("/share/scenario/{token}", tags=["Share"],
              summary="Get info of the shared scenario")
def get_share_scenario_info(
        auth_context: AuthContextShareLink = Depends(ShareTokenAuth.get_and_check_share_link_token_from_url)) -> ShareScenarioInfoReponseDTO:
    return ShareService.get_scenario_entity_object_info(auth_context.get_share_link())


# Open route to zip the resource of a shared scenario
@core_app.post("/share/scenario/{token}/resource/{resource_id}/zip", tags=["Share"],
               summary="Zip the resource of a shared scenario")
def zip_scenario_resource(resource_id: str, auth_context: AuthContextShareLink = Depends(
        ShareTokenAuth.get_and_check_share_link_token_from_url)) -> ShareResourceZippedResponseDTO:
    return ShareService.zip_shared_scenario_resource(auth_context.get_share_link(), resource_id)


# Open route to download a resource
@core_app.get("/share/scenario/{token}/resource/{resource_id}/download",
              tags=["Share"], summary="Download the resource of a shared scenario")
def download_scenario_resource(
        resource_id: str, auth_context: AuthContextShareLink = Depends(ShareTokenAuth.get_and_check_share_link_token_from_url)) -> FileResponse:
    file_path = ShareService.download_scenario_resource(auth_context.get_share_link(), resource_id)
    return FileHelper.create_file_response(file_path)


###################################### VIEW ######################################
@core_app.post("/share/resource/views/{view_name}", tags=["Resource"],
               summary="Call the view name for a resource")
def call_view_on_resource(
        view_name: str, call_view_params: CallViewParams,
        auth_context: AuthContextShareLink = Depends(AuthorizationService.check_share_link)) -> CallViewResultDTO:

    return ShareService.call_resource_view(
        auth_context.get_share_link(), view_name, call_view_params).to_dto()
