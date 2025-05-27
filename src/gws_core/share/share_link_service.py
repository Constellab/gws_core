

from typing import List, Optional

from gws_core.core.classes.paginator import Paginator
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model import Model
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_space_access import ShareLinkSpaceAccessService
from gws_core.share.shared_dto import (GenerateShareLinkDTO,
                                       GenerateUserAccessTokenForSpaceResponse,
                                       ShareLinkEntityType, ShareLinkType,
                                       UpdateShareLinkDTO)
from gws_core.user.user_dto import UserFullDTO
from gws_core.user.user_service import UserService


class ShareLinkService:

    @classmethod
    def find_by_type_and_entity(cls, entity_type: ShareLinkEntityType,
                                entity_id: str,
                                link_type: ShareLinkType) -> Optional[ShareLink]:
        """Method that find a shared entity link by its entity id and type
        """

        return ShareLink.find_by_entity_type_and_id(entity_type, entity_id, link_type)

    @classmethod
    def find_by_token_and_check_validity(cls, token: str) -> ShareLink:
        """Method that find a shared entity link by its token and check if it is valid
        """
        share_link = ShareLink.find_by_token_and_check(token)

        if not share_link.is_valid():
            raise BadRequestException("The link is expired")

        return share_link

    @classmethod
    def find_by_token_and_check(cls, token: str) -> 'ShareLink':
        return ShareLink.find_by_token_and_check(token)

    @classmethod
    def generate_share_link(cls, share_dto: GenerateShareLinkDTO, link_type: ShareLinkType) -> ShareLink:
        """Method that generate a share link for a given entity
        """

        if link_type == ShareLinkType.SPACE:
            if share_dto.entity_type != ShareLinkEntityType.RESOURCE:
                raise BadRequestException("Only resource can be shared with space")

        existing_link = ShareLink.find_by_entity_type_and_id(
            entity_type=share_dto.entity_type, entity_id=share_dto.entity_id,
            link_type=link_type)

        if existing_link:
            raise BadRequestException("Share link already exists for this object")

        model: Model = ShareLink.get_model_and_check(share_dto.entity_id, share_dto.entity_type)

        share_link_model = ShareLink()
        share_link_model.entity_id = model.id
        share_link_model.entity_type = share_dto.entity_type
        share_link_model.valid_until = share_dto.valid_until
        share_link_model.token = StringHelper.generate_uuid() + '_' + str(DateHelper.now_utc_as_milliseconds())
        share_link_model.link_type = link_type

        return share_link_model.save()

    @classmethod
    def update_share_link(cls, id_: str, share_dto: UpdateShareLinkDTO) -> ShareLink:
        """Method that update a share link for a given entity
        """

        shared_entity_link: ShareLink = ShareLink.get_by_id_and_check(id_)

        shared_entity_link.valid_until = share_dto.valid_until
        return shared_entity_link.save()

    @classmethod
    def get_or_create_valid_public_share_link(cls, share_dto: GenerateShareLinkDTO) -> ShareLink:
        return cls.get_or_create_valid_share_link(share_dto, ShareLinkType.PUBLIC)

    @classmethod
    def get_or_create_valid_share_link(cls, share_dto: GenerateShareLinkDTO,
                                       link_type: ShareLinkType) -> ShareLink:
        """Method that get a valid share link for a given entity or create a new one if it does not exist or expired
        """

        existing_link = ShareLink.find_by_entity_type_and_id(
            entity_type=share_dto.entity_type, entity_id=share_dto.entity_id,
            link_type=link_type)

        if existing_link:
            if existing_link.is_valid_at(share_dto.valid_until):
                return existing_link
            else:
                existing_link.valid_until = share_dto.valid_until
                return existing_link.save()
        else:
            return cls.generate_share_link(share_dto, link_type)

    @classmethod
    def delete_share_link(cls, id_: str) -> None:
        """Method that delete a share link for a given entity
        """

        ShareLink.delete_by_id(id_)

    @classmethod
    def get_shared_links(cls, page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ShareLink]:
        """Method that return the shared links
        """

        query = ShareLink.select().order_by(ShareLink.valid_until.asc())

        paginator: Paginator[ShareLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def clean_links(cls, clean_expired_links: bool = True, clean_invalid_links: bool = True) -> None:
        """ Method that clean the shared links

        :param clean_expired_links: If true delete the expired links, defaults to True
        :type clean_expired_links: bool, optional
        :param clean_invalid_links: If true delete links where model does not exist anymore, defaults to True
        :type clean_invalid_links: bool, optional
        """
        if not clean_expired_links and not clean_invalid_links:
            return

        links: List[ShareLink] = ShareLink.select()

        for link in links:
            if clean_expired_links and not link.is_valid():
                link.delete_instance()
            elif clean_invalid_links and link.get_model(link.entity_id, link.entity_type) is None:
                link.delete_instance()

    @classmethod
    def generate_user_access_token_for_space_link(
            cls, token: str, user: UserFullDTO) -> GenerateUserAccessTokenForSpaceResponse:
        """Method called from Space to generate a user access token for a space link.
        As this is called by space, the user is authenticated
        """

        share_link = ShareLinkService.find_by_token_and_check_validity(token)

        if share_link.link_type != ShareLinkType.SPACE:
            raise BadRequestException("The link is not a space link")

        if share_link.entity_type != ShareLinkEntityType.RESOURCE:
            raise BadRequestException("The link is not for a resource")

        # Update the user information in the database
        UserService.create_or_update_user_dto(user)

        share_link_access = ShareLinkSpaceAccessService.generate_share_link_space_access(
            share_link.id, user.id)

        access_url = share_link.get_space_link(share_link_access.user_access_token)
        return GenerateUserAccessTokenForSpaceResponse(
            # return the main share link valid until date
            share_link_valid_until=share_link.valid_until,
            access_url=access_url,
            access_url_valid_until=share_link_access.valid_until
        )
