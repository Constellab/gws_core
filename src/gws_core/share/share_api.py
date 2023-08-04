# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core_app import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.share.share_link import ShareLinkType
from gws_core.user.auth_service import AuthService

from .share_service import ShareService


# Open to mark the resource as downloaded by another lab
@core_app.post("/share/{entity_type}/mark-as-shared/{token}", tags=["Share"],
               summary="Mark the resource as downloaded by another lab")
def mark_entity_as_shared(entity_type: ShareLinkType, token: str, destination: dict) -> None:
    ShareService.mark_entity_as_shared(entity_type, token, destination)


@core_app.get("/share/{entity_type}/{entity_id}/shared-to", tags=["Share"],
              summary="Get info about which lab this object was shared to", response_model=None)
def get_shared_to_list(entity_type: ShareLinkType,
                       entity_id: str,
                       _=Depends(AuthService.check_user_access_token)) -> dict:
    return ShareService.get_shared_to_list(entity_type, entity_id).to_json()


################################ RESOURCE ################################


# Open route to download a resource
@core_app.get("/share/resource/download/{token}", tags=["Share"], summary="Download a resource")
def download_resource(token: str) -> FileResponse:
    zip_path = ShareService.zip_resource_from_token(token)
    return FileHelper.create_file_response(zip_path)
