

from typing import Dict, NoReturn, Optional, Type, TypeVar

import requests
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException

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
        # For app context, we force the access token
        if CurrentUserService.is_app_context():
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

     #################################### ERROR HANDLING ####################################

    def handle_error(self, error: Exception, operation_description: str) -> NoReturn:
        """
        Centralized error handler for all space service operations.
        Converts connection errors to user-friendly messages.

        :param error: The exception that was raised
        :type error: Exception
        :param operation_description: Description of the operation that failed (e.g., "create folder", "save scenario")
        :type operation_description: str
        :raises BadRequestException: When space is not available (connection error)
        :raises BaseHTTPException: For other HTTP-related errors
        """
        if isinstance(error, requests.exceptions.ConnectionError):
            raise BadRequestException(
                f"Can't {operation_description}, space is not available. "
                "Please ensure the space server is running and accessible."
            )
        elif isinstance(error, BaseHTTPException):
            # Re-raise HTTP exceptions with additional context
            error.detail = f"Can't {operation_description}. Error: {error.detail}"
            raise error
        else:
            # For any other unexpected errors, wrap them in a BadRequestException
            raise BadRequestException(
                f"Can't {operation_description}. Unexpected error: {str(error)}"
            )
