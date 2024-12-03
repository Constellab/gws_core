

from gws_core.share.share_link import ShareLink
from gws_core.share.share_link_service import ShareLinkService


class ShareTokenAuth:
    """Class to manage authentication with share token for share controller
    """

    @classmethod
    def get_and_check_token(cls, token: str) -> ShareLink:
        return ShareLinkService.find_by_token_and_check_validity(token)
