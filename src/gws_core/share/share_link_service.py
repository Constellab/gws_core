

from typing import Optional

from gws_core.core.classes.paginator import Paginator
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model import Model
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import GenerateShareLinkDTO, ShareLinkType


class ShareLinkService:

    @classmethod
    def find_by_entity_id_and_type(
            cls, entity_type: ShareLinkType, entity_id: str) -> Optional[ShareLink]:
        """Method that find a shared entity link by its entity id and type
        """

        return ShareLink.find_by_entity_type_and_id(entity_type, entity_id)

    @classmethod
    def find_by_token_and_check_validity(cls, token: str) -> ShareLink:
        """Method that find a shared entity link by its token and check if it is valid
        """
        share_link = ShareLink.find_by_token_and_check(token)

        if share_link.valid_until < DateHelper.now_utc():
            raise BadRequestException("The link is expired")

        return share_link

    @classmethod
    def find_by_token_and_check(cls, token: str) -> 'ShareLink':
        return ShareLink.find_by_token_and_check(token)

    @classmethod
    def generate_share_link(cls, share_dto: GenerateShareLinkDTO) -> ShareLink:
        """Method that generate a share link for a given entity
        """

        existing_link = ShareLink.find_by_entity_type_and_id(
            entity_type=share_dto.entity_type, entity_id=share_dto.entity_id)

        if existing_link:
            raise BadRequestException("Share link already exists for this object")

        model: Model = ShareLink.get_model_and_check(share_dto.entity_id, share_dto.entity_type)

        shared_link_model = ShareLink()
        shared_link_model.entity_id = model.id
        shared_link_model.entity_type = share_dto.entity_type
        shared_link_model.valid_until = share_dto.valid_until
        shared_link_model.token = StringHelper.generate_uuid() + '_' + str(DateHelper.now_utc_as_milliseconds())

        return shared_link_model.save()

    @classmethod
    def update_share_link(cls, share_dto: GenerateShareLinkDTO) -> ShareLink:
        """Method that update a share link for a given entity
        """

        shared_entity_link: ShareLink = ShareLink.find_by_entity_type_and_id_and_check(
            share_dto.entity_type, share_dto.entity_id)

        shared_entity_link.valid_until = share_dto.valid_until
        return shared_entity_link.save()

    @classmethod
    def delete_share_link(cls, id: str) -> None:
        """Method that delete a share link for a given entity
        """

        ShareLink.delete_by_id(id)

    @classmethod
    def get_shared_links(cls, page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ShareLink]:
        """Method that return the shared links
        """

        query = ShareLink.select().order_by(ShareLink.valid_until.asc())

        paginator: Paginator[ShareLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator
