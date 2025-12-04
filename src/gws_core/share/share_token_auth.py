from gws_core.user.auth_context import AuthContextShareLink
from gws_core.user.authorization_service import AuthorizationService


class ShareTokenAuth:
    """Class to manage authentication with share token for share controller"""

    @classmethod
    def get_and_check_share_link_token_from_url(cls, token: str) -> AuthContextShareLink:
        """Method to get and check the share token from the url

        If the header gws_user_access_token is present, it will be used to check the the access for the user
        """

        return AuthorizationService.auth_share_link_from_token(token)
