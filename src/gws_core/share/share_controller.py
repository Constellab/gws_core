

from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core.model.model_dto import PageDTO
from gws_core.core.service.external_lab_dto import ExternalLabWithUserInfo
from gws_core.core_controller import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.resource_controller import CallViewParams
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.share.share_token_auth import ShareTokenAuth
from gws_core.share.shared_dto import (ShareEntityInfoDTO, ShareLinkType,
                                       ShareResourceInfoReponseDTO,
                                       ShareResourceZippedResponseDTO,
                                       ShareScenarioInfoReponseDTO)
from gws_core.user.auth_service import AuthService

from .share_service import ShareService


# Open to mark the resource as downloaded by another lab
@core_app.post("/share/{entity_type}/mark-as-shared/{token}", tags=["Share"],
               summary="Mark the resource as downloaded by another lab")
def mark_entity_as_shared(entity_type: ShareLinkType, receiver_lab: ExternalLabWithUserInfo,
                          share_link=Depends(ShareTokenAuth.get_and_check_token)) -> None:
    ShareService.mark_entity_as_shared(entity_type, share_link, receiver_lab)


@core_app.get("/share/{entity_type}/{entity_id}/shared-to", tags=["Share"],
              summary="Get info about which lab this object was shared to", response_model=None)
def get_shared_to_list(entity_type: ShareLinkType,
                       entity_id: str,
                       _=Depends(AuthService.check_user_access_token)) -> PageDTO[ShareEntityInfoDTO]:
    return ShareService.get_shared_to_list(entity_type, entity_id).to_dto()


################################ RESOURCE ################################
# Open route to get info about a shared entity
# TODO TO REMOVE ONCE MOST LAST ARE ON V 0.10.4
@core_app.get("/share/info/{token}", tags=["Share"],
              summary="Get info about a shared entity")
def get_share_entity_info(share_link=Depends(ShareTokenAuth.get_and_check_token)) -> ShareResourceInfoReponseDTO:
    return ShareService.get_resource_entity_object_info(share_link)


# Same as above
@core_app.get("/share/resource/{token}", tags=["Share"], summary="Download a resource")
def get_share_resource_info(share_link=Depends(ShareTokenAuth.get_and_check_token)) -> ShareResourceInfoReponseDTO:
    return ShareService.get_resource_entity_object_info(share_link)


# Open zip the shared entity
@core_app.post("/share/resource/{token}/zip", tags=["Share"], summary="Zip the shared entity")
def zip_resource(share_link=Depends(ShareTokenAuth.get_and_check_token)) -> ShareResourceZippedResponseDTO:
    return ShareService.zip_shared_resource(share_link)


# Open route to download a resource
@core_app.get("/share/resource/{token}/download", tags=["Share"], summary="Download a zipped entity")
def download_resource(share_link=Depends(ShareTokenAuth.get_and_check_token)) -> FileResponse:
    file_path = ShareService.download_zipped_resource(share_link)
    return FileHelper.create_file_response(file_path)


@core_app.post("/share/resource/{token}/views/{view_name}", tags=["Resource"],
               summary="Call the view name for a resource")
def call_view_on_resource(view_name: str,
                          call_view_params: CallViewParams,
                          share_link=Depends(ShareTokenAuth.get_and_check_token)) -> CallViewResultDTO:

    return ShareService.call_resource_view(
        share_link, view_name, call_view_params).to_dto()


################################ SCENARIO ################################

# Open zip the resource of a shared scenario
@core_app.get("/share/scenario/{token}", tags=["Share"],
              summary="Get info of the shared scenario")
def get_share_scenario_info(share_link=Depends(ShareTokenAuth.get_and_check_token)) -> ShareScenarioInfoReponseDTO:
    return ShareService.get_scenario_entity_object_info(share_link)

# Open zip the resource of a shared scenario


@core_app.post("/share/scenario/{token}/resource/{resource_id}/zip", tags=["Share"],
               summary="Zip the resource of a shared scenario")
def zip_scenario_resource(resource_id: str,
                          share_link=Depends(ShareTokenAuth.get_and_check_token)) -> ShareResourceZippedResponseDTO:
    return ShareService.zip_shared_scenario_resource(share_link, resource_id)


# Open route to download a resource
@core_app.get("/share/scenario/{token}/resource/{resource_id}/download",
              tags=["Share"], summary="Download the resource of a shared scenario")
def download_scenario_resource(resource_id: str,
                               share_link=Depends(ShareTokenAuth.get_and_check_token)) -> FileResponse:
    file_path = ShareService.download_scenario_resource(share_link, resource_id)
    return FileHelper.create_file_response(file_path)
