# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core.classes.paginator import Paginator
from gws_core.core_app import core_app
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


# Open route to download a resource
@core_app.get("/share/resource/download/{token}", tags=["Share"], summary="Download a resource")
def download_resource(token: str) -> FileResponse:
    return ShareService.download_resource(token)
