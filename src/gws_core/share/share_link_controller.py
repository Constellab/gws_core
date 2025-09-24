

from typing import Optional

from fastapi import Depends

from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.core_controller import core_app
from gws_core.share.share_link_service import ShareLinkService
from gws_core.user.authorization_service import AuthorizationService

from .shared_dto import (GenerateShareLinkDTO, ShareLinkDTO,
                         ShareLinkEntityType, ShareLinkType,
                         UpdateShareLinkDTO)


@core_app.post("/share-link/public", tags=["Share"], summary="Generate a public share link for an entity")
def generate_public_share_link(share_dto: GenerateShareLinkDTO,
                               _=Depends(AuthorizationService.check_user_access_token)) -> ShareLinkDTO:
    return ShareLinkService.generate_share_link(share_dto, ShareLinkType.PUBLIC).to_dto()


@core_app.put("/share-link/{id_}", tags=["Share"], summary="Update a share link for an entity")
def update_share_link(id_: str,
                      update_dto: UpdateShareLinkDTO,
                      _=Depends(AuthorizationService.check_user_access_token)) -> ShareLinkDTO:
    return ShareLinkService.update_share_link(id_, update_dto).to_dto()


@core_app.delete("/share-link/{id_}", tags=["Share"], summary="Delete a shared link")
def delete_share_link(id_: str,
                      _=Depends(AuthorizationService.check_user_access_token)) -> None:
    ShareLinkService.delete_share_link(id_)


@core_app.get("/share-link", tags=["Share"], summary="Get share links")
def get_share_links(page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthorizationService.check_user_access_token)) -> PageDTO[ShareLinkDTO]:
    return ShareLinkService.get_shared_links(page, number_of_items_per_page).to_dto()


@core_app.get(
    "/share-link/{entity_type}/{entity_id}/{link_type}", tags=["Share"],
    summary="Get share entity")
def get_share_entity(entity_type: ShareLinkEntityType, entity_id: str,
                     link_type: ShareLinkType,
                     _=Depends(AuthorizationService.check_user_access_token)) -> Optional[ShareLinkDTO]:
    share_link = ShareLinkService.find_by_type_and_entity(entity_type, entity_id, link_type)
    return share_link.to_dto() if share_link else None


class CleanLinksDTO(BaseModelDTO):
    clean_expired_links: bool
    clean_invalid_links: bool


@core_app.post("/share-link/clean", tags=["Share"], summary="Clean links")
def clean_share_links(clean_links_dto: CleanLinksDTO,
                      _=Depends(AuthorizationService.check_user_access_token)) -> None:
    ShareLinkService.clean_links(clean_links_dto.clean_expired_links, clean_links_dto.clean_invalid_links)
