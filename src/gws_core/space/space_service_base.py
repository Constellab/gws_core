

from typing import Dict, Optional, Type, TypeVar

from ..core.utils.settings import Settings
from ..user.current_user_service import CurrentUserService
from ..user.user import User

SpaceServiceBaseType = TypeVar('SpaceServiceBaseType', bound='SpaceServiceBase')


class SpaceServiceBase():
    AUTH_HEADER_KEY: str = 'Authorization'
    AUTH_API_KEY_HEADER_PREFIX: str = 'api-key'
    # Key to set the user in the request
    USER_ID_HEADER_KEY: str = 'User'

    ACCESS_TOKEN_HEADER = 'access-token'

    _access_token: Optional[str] = None

    def __init__(self, access_token: Optional[str] = None):
        """ Constructor of the SpaceService

        :param access_token: if access token is provided, it is used to authenticate.
        Otherwise the current user is used for authentication, defaults to None
        :type access_token: Optional[str], optional
        """
        self._access_token = access_token

    @classmethod
    def get_instance(cls: Type[SpaceServiceBaseType]) -> SpaceServiceBaseType:
        """
        Return a new instance of the SpaceService that use the
        current user for authentication

        :return: a new instance of the SpaceService
        :rtype: SpaceService
        """
        # For streamlit context, we force the access token
        if CurrentUserService.is_streamlit_context():
            return cls.create_with_access_token()

        return cls()

    # TODO TO REMOVE
    @classmethod
    def create_with_access_token(cls: Type[SpaceServiceBaseType]) -> SpaceServiceBaseType:
        """
        Return a new instance of the SpaceService that use the
        access token for authentication

        :return: a new instance of the SpaceService
        :rtype: SpaceService
        """

        # for now we fake an access token.
        # In the future, the access token will be passed as parameter
        # It allow to add the header in the request to switch to a access token request
        return cls('1')

    #################################### OTHER ####################################

    def _get_space_api_url(self, route: str) -> str:
        """
        Build an URL to call the space API
        """

        space_api_url = Settings.get_space_api_url()
        return space_api_url + '/' + route

    def _get_request_header(self) -> Dict[str, str]:
        """
        Return the header for a request to space, with Api key and User if exists
        """
        # Header with the Api Key
        headers = {self.AUTH_HEADER_KEY: self.AUTH_API_KEY_HEADER_PREFIX +
                   ' ' + Settings.get_space_api_key()}

        user: User = CurrentUserService.get_current_user()

        if user:
            headers[self.USER_ID_HEADER_KEY] = user.id

        if self._access_token:
            headers[self.ACCESS_TOKEN_HEADER] = self._access_token

        return headers
