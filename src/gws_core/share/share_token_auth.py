

from fastapi import Request

from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_service import ShareLinkService
from gws_core.user.auth_service import AuthService


class ShareTokenAuth:
    """Class to manage authentication with share token for share controller
    """

    @classmethod
    def get_and_check_token(cls, token: str, request: Request) -> ShareLink:
        share_link = ShareLinkService.find_by_token_and_check_validity(token)

        # try to authenticate the user if the user token is provided
        # this is optional
        AuthService.authenticate_user_if_token_provided(request)

        return share_link
