

from fastapi import Request

from gws_core.core.exception.exceptions.forbidden_exception import \
    ForbiddenException
from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.share_link_space_access import ShareLinkSpaceAccessService
from gws_core.share.shared_dto import ShareLinkType
from gws_core.user.auth_service import AuthService


class ShareTokenAuth:
    """Class to manage authentication with share token for share controller
    """

    @classmethod
    def get_and_check_token(cls, token: str, request: Request) -> ShareLink:
        """Method to get and check the share token from the request

        If the header gws_user_access_token is present, it will be used to check the the access for the user
        """

        share_link = ShareLinkService.find_by_token_and_check_validity(token)

        # if the link is a space access link, check if the user access token is valid
        if share_link.link_type == ShareLinkType.SPACE:
            user_access_token = request.headers.get("gws_user_access_token")
            if not user_access_token:
                raise ForbiddenException("This link requires authentication")
            space_access_info = ShareLinkSpaceAccessService.find_by_token_and_check_validity(
                user_access_token, share_link.id)

            AuthService.authenticate(space_access_info.user_id)

        return share_link
