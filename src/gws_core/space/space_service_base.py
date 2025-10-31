

from typing import Callable, Dict, List, NoReturn, Optional, Type, TypeVar

import requests
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.core.model.model_dto import BaseModelDTO, PageDTO

from ..core.utils.settings import Settings
from ..user.current_user_service import CurrentUserService
from ..user.user import User

SpaceServiceBaseType = TypeVar('SpaceServiceBaseType', bound='SpaceServiceBase')
T = TypeVar('T', bound=BaseModelDTO)


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

    #################################### PAGE DTO CONVERSION ####################################

    @staticmethod
    def build_page_dto_from_space_json(
            json_data: dict,
            object_converter: Callable[[dict], T]) -> PageDTO[T]:
        """Build a PageDTO from Space API JSON response format (ClPageI).

        The Space API returns paginated data in the ClPageI format:
        {
            "objects": T[],
            "first": boolean,
            "last": boolean,
            "totalElements": number,
            "currentPage": number,
            "pageSize": number,
            "totalIsApproximate"?: boolean
        }

        This method converts it to the internal PageDTO format.

        :param json_data: The JSON response from the Space API
        :type json_data: dict
        :param object_converter: Function to convert each object in the list from JSON to the target DTO type
        :type object_converter: Callable[[dict], T]
        :return: PageDTO with converted objects
        :rtype: PageDTO[T]
        """
        current_page = json_data.get('currentPage', 0)
        page_size = json_data.get('pageSize', 20)
        total_elements = json_data.get('totalElements', 0)
        is_first = json_data.get('first', True)
        is_last = json_data.get('last', True)
        total_is_approximate = json_data.get('totalIsApproximate', False)

        # Convert objects using the provided converter function
        objects_json = json_data.get('objects', [])
        objects = [object_converter(obj) for obj in objects_json]

        # Calculate pagination metadata
        total_pages = max(1, (total_elements + page_size - 1) // page_size) if page_size > 0 else 1
        prev_page = max(0, current_page - 1)
        next_page = min(total_pages - 1, current_page + 1)
        last_page = max(0, total_pages - 1)

        return PageDTO[T](
            page=current_page,
            prev_page=prev_page,
            next_page=next_page,
            last_page=last_page,
            total_number_of_items=total_elements,
            total_number_of_pages=total_pages,
            number_of_items_per_page=page_size,
            is_first_page=is_first,
            is_last_page=is_last,
            total_is_approximate=total_is_approximate,
            objects=objects
        )

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
