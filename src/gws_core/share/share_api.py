# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi import Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from gws_core.core.classes.paginator import Paginator
from gws_core.core_app import core_app
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from .share_service import ShareService
from .shared_dto import GenerateShareLinkDTO
from .shared_entity import SharedEntityLink


@core_app.post("/share", tags=["Share"], summary="Generate a share link for an entity")
def generate_share_link(share_dto: GenerateShareLinkDTO,
                        _: UserData = Depends(AuthService.check_user_access_token)) -> SharedEntityLink:
    return ShareService.generate_share_link(share_dto).to_json()


@core_app.put("/share", tags=["Share"], summary="Update a share link for an entity")
def update_share_link(share_dto: GenerateShareLinkDTO,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> SharedEntityLink:
    return ShareService.update_share_link(share_dto).to_json()


@core_app.delete("/share/{id}", tags=["Share"], summary="Delete a shared link")
def delete_share_link(id: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    return ShareService.delete_share_link(id)


@core_app.get("/share", tags=["Share"], summary="Get share links")
def get_share_links(page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _: UserData = Depends(AuthService.check_user_access_token)) -> Paginator:
    return ShareService.get_shared_links(page, number_of_items_per_page).to_json()


@core_app.get("/share/{entity_type}/{entity_id}", tags=["Share"], summary="Get share entity")
def get_share_entity(entity_type: str, entity_id: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> SharedEntityLink:
    share_link = ShareService.find_by_entity_id_and_type(entity_type, entity_id)
    return share_link.to_json() if share_link else None


# Open route to download a resource
@core_app.get("/share/resource/download/{token}", tags=["Share"], summary="Download a resource")
def download_resource(token: str) -> FileResponse:
    zip_path = ShareService.download_resource(token)
    return FileHelper.create_file_response(zip_path)


# Open to mark the resource as downloaded by another lab
@core_app.post("/share/resource/mark-as-downloaded/{token}", tags=["Share"],
               summary="Mark the resource as downloaded by another lab")
def mark_resource_as_downloaded(token: str, destination: dict) -> FileResponse:
    return ShareService.mark_resource_as_downloaded(token, destination)


class ImportDto(BaseModel):
    url: str


@core_app.post("/share/resource/import", tags=["Share"], summary="Download a resource")
def import_resource(import_dto: ImportDto,
                    _: UserData = Depends(AuthService.check_user_access_token)) -> ResourceModel:
    return ShareService.copy_external_resource(import_dto.url).to_json()
