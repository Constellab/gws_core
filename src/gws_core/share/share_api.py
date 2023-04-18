# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from gws_core.core.classes.paginator import Paginator
from gws_core.core_app import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.resource_model import ResourceModel
from gws_core.share.share_link import ShareLinkType
from gws_core.share.shared_resource import SharedResource
from gws_core.user.auth_service import AuthService

from .share_service import ShareService


# Open to mark the resource as downloaded by another lab
@core_app.post("/share/{entity_type}/mark-as-shared/{token}", tags=["Share"],
               summary="Mark the resource as downloaded by another lab")
def mark_entity_as_shared(entity_type: ShareLinkType, token: str, destination: dict) -> None:
    return ShareService.mark_entity_as_shared(entity_type, token, destination)


@core_app.get("/share/{entity_type}/{entity_id}/shared-to", tags=["Share"],
              summary="Get info about which lab this object was shared to", response_model=None)
def get_shared_to_list(entity_type: ShareLinkType,
                       entity_id: str,
                       _=Depends(AuthService.check_user_access_token)) -> Paginator[SharedResource]:
    return ShareService.get_shared_to_list(entity_type, entity_id).to_json()


class ImportDto(BaseModel):
    url: str

################################ RESOURCE ################################


@core_app.post("/share/resource/import", tags=["Share"], summary="Download a resource", response_model=None)
def import_resource(import_dto: ImportDto,
                    _=Depends(AuthService.check_user_access_token)) -> ResourceModel:
    return ShareService.download_resource_from_external_lab(import_dto.url).to_json()


# Open route to download a resource
@core_app.get("/share/resource/download/{token}", tags=["Share"], summary="Download a resource")
def download_resource(token: str) -> FileResponse:
    zip_path = ShareService.zip_resource_from_token(token)
    return FileHelper.create_file_response(zip_path)
