from typing import TypeVar

from ..core.utils.settings import Settings
from ..user.current_user_service import CurrentUserService
from ..user.user import User

LabManagerServiceBaseType = TypeVar("LabManagerServiceBaseType", bound="LabManagerServiceBase")


class LabManagerServiceBase:
    AUTH_HEADER_KEY: str = "Authorization"
    AUTH_API_KEY_HEADER_PREFIX: str = "api-key"
    # Key to set the user in the request
    USER_ID_HEADER_KEY: str = "User"

    ACCESS_TOKEN_HEADER = "access-token"

    _access_token: str | None = None

    def __init__(self, access_token: str | None = None):
        """Constructor of the SpaceService

        :param access_token: if access token is provided, it is used to authenticate.
        Otherwise the current user is used for authentication, defaults to None
        :type access_token: Optional[str], optional
        """
        self._access_token = access_token

    @classmethod
    def get_instance(cls: type[LabManagerServiceBaseType]) -> LabManagerServiceBaseType:
        """
        Return a new instance of the SpaceService that use the
        current user for authentication

        :return: a new instance of the SpaceService
        :rtype: SpaceService
        """
        return cls()

    #################################### OTHER ####################################

    def _get_lab_manager_api_url(self, route: str) -> str:
        """
        Build an URL to call the lab manager API
        """
        lab_api_url = Settings.get_lab_manager_api_url()
        return lab_api_url + "/" + route

    def _get_request_header(self) -> dict[str, str]:
        """
        Return the header for a request to lab manager, with Api key and User if exists
        """
        # Header with the Api Key
        headers = {
            self.AUTH_HEADER_KEY: self.AUTH_API_KEY_HEADER_PREFIX
            + " "
            + Settings.get_space_api_key()
        }

        user: User = CurrentUserService.get_current_user()

        if user:
            headers[self.USER_ID_HEADER_KEY] = user.id

        if self._access_token:
            headers[self.ACCESS_TOKEN_HEADER] = self._access_token

        return headers
