# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from fastapi import Depends

from gws_core.core.classes.paginator import Paginator
from gws_core.core_app import core_app
from gws_core.share.share_link_service import ShareLinkService
from gws_core.user.auth_service import AuthService

from .share_link import ShareLink
from .shared_dto import GenerateShareLinkDTO


@core_app.post("/share-link", tags=["Share"], summary="Generate a share link for an entity", response_model=None)
def generate_share_link(share_dto: GenerateShareLinkDTO,
                        _=Depends(AuthService.check_user_access_token)) -> ShareLink:
    return ShareLinkService.generate_share_link(share_dto).to_json()


@core_app.put("/share-link", tags=["Share"], summary="Update a share link for an entity", response_model=None)
def update_share_link(share_dto: GenerateShareLinkDTO,
                      _=Depends(AuthService.check_user_access_token)) -> ShareLink:
    return ShareLinkService.update_share_link(share_dto).to_json()


@core_app.delete("/share-link/{id}", tags=["Share"], summary="Delete a shared link")
def delete_share_link(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> None:
    return ShareLinkService.delete_share_link(id)


@core_app.get("/share-link", tags=["Share"], summary="Get share links", response_model=None)
def get_share_links(page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> Paginator:
    return ShareLinkService.get_shared_links(page, number_of_items_per_page).to_json()


@core_app.get("/share-link/{entity_type}/{entity_id}", tags=["Share"], summary="Get share entity", response_model=None)
def get_share_entity(entity_type: str, entity_id: str,
                     _=Depends(AuthService.check_user_access_token)) -> ShareLink:
    share_link = ShareLinkService.find_by_entity_id_and_type(entity_type, entity_id)
    return share_link.to_json() if share_link else None
