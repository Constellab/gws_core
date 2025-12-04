from datetime import datetime, timedelta
from typing import List

from gws_core.core.exception.exceptions.forbidden_exception import ForbiddenException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper


class ShareLinkSpaceAccess(BaseModelDTO):
    """DTO for share link of type space access"""

    user_access_token: str
    valid_until: datetime
    share_link_id: str
    user_id: str


class ShareLinkSpaceAccessService:
    """Service to generate access token for share link of type space access

    The space API call it before opening a Resource in a space to check
    generate a token to access the resource. Then the token is used to access the resource.
    """

    accesses: List[ShareLinkSpaceAccess] = []

    # The duration of the access token
    # 1 hour, (just the time to test)
    ACCESS_DURATION = 60 * 60

    @classmethod
    def generate_share_link_space_access(
        cls, share_link_id: str, user_id: str
    ) -> ShareLinkSpaceAccess:
        """Generate a share link space access token"""

        access = ShareLinkSpaceAccess(
            user_access_token=StringHelper.generate_uuid()
            + "_"
            + str(DateHelper.now_utc_as_milliseconds()),
            valid_until=datetime.now() + timedelta(seconds=cls.ACCESS_DURATION),
            share_link_id=share_link_id,
            user_id=user_id,
        )
        cls._add_access(access)

        return access

    @classmethod
    def find_by_token_and_check_validity(
        cls, user_access_token: str, share_link_id: str
    ) -> ShareLinkSpaceAccess:
        """Find a share link space access by its token and check if it is valid"""

        access = next(
            (access for access in cls.accesses if access.user_access_token == user_access_token),
            None,
        )

        if not access:
            raise ForbiddenException("Invalid link. User not authenticated")

        if access.share_link_id != share_link_id:
            raise ForbiddenException("Invalid link. User not authenticated")

        if access.valid_until < datetime.now():
            raise ForbiddenException("Link expired")

        return access

    @classmethod
    def _add_access(cls, access: ShareLinkSpaceAccess) -> None:
        """Add an access to the list of accesses"""

        # clean the list of accesses
        cls.accesses = [access for access in cls.accesses if access.valid_until > datetime.now()]

        # remove access for the same user and link
        cls.accesses = [
            access
            for access in cls.accesses
            if access.user_id != access.user_id and access.share_link_id != access.share_link_id
        ]

        cls.accesses.append(access)
