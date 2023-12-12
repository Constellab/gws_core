# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core.model.model_dto import PageDTO
from gws_core.core.service.external_lab_service import ExternalLabWithUserInfo
from gws_core.core_controller import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.share.shared_dto import (ShareEntityInfoDTO,
                                       ShareEntityInfoReponseDTO,
                                       ShareEntityZippedResponseDTO,
                                       ShareLinkType)
from gws_core.user.auth_service import AuthService

from .share_service import ShareService


# Open to mark the resource as downloaded by another lab
@core_app.post("/share/{entity_type}/mark-as-shared/{token}", tags=["Share"],
               summary="Mark the resource as downloaded by another lab")
def mark_entity_as_shared(entity_type: ShareLinkType, token: str, receiver_lab: ExternalLabWithUserInfo) -> None:
    ShareService.mark_entity_as_shared(entity_type, token, receiver_lab)


@core_app.get("/share/{entity_type}/{entity_id}/shared-to", tags=["Share"],
              summary="Get info about which lab this object was shared to", response_model=None)
def get_shared_to_list(entity_type: ShareLinkType,
                       entity_id: str,
                       _=Depends(AuthService.check_user_access_token)) -> PageDTO[ShareEntityInfoDTO]:
    return ShareService.get_shared_to_list(entity_type, entity_id).to_dto()


# Open route to get info about a shared entity
@core_app.get("/share/info/{token}", tags=["Share"],
              summary="Get info about a shared entity")
def get_share_entity_info(token: str) -> ShareEntityInfoReponseDTO:
    return ShareService.get_share_entity_info(token)


# Open zip the shared entity
@core_app.post("/share/zip-entity/{token}", tags=["Share"], summary="Zip the shared entity")
def zip_entity(token: str) -> ShareEntityZippedResponseDTO:
    return ShareService.zip_shared_entity(token)


# Open route to download a resource
@core_app.get("/share/download/{token}/{zipped_entity_id}", tags=["Share"], summary="Download a zipped entity")
def download_resource(token: str, zipped_entity_id: str) -> FileResponse:
    file_path = ShareService.download_zipped_entity(token, zipped_entity_id)
    return FileHelper.create_file_response(file_path)

################################ RESOURCE ################################


# Open route to download a resource
@core_app.get("/share/resource/download/{token}", tags=["Share"], summary="Download a resource")
def old_download_resource(token: str) -> FileResponse:
    raise Exception("The shared link is deprecated, please regenerate it in the new gws_core v0.6.1 or more")
