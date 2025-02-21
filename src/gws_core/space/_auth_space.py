from fastapi import Depends

from gws_core.user.auth_service import AuthService

from ..core.exception.exceptions import UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from ._oauth2_space_header_scheme import (space_api_key_header,
                                          space_header_api_user_header)
from .space_service import SpaceService


class AuthSpace:

    @classmethod
    def check_space_api_key(cls, api_key: str = Depends(space_api_key_header)) -> None:
        """Method to check the space api key in the request header

        :param api_key: [description], defaults to Depends(oauth2_space_header_scheme)
        :type api_key: str, optional
        :raises UnauthorizedException: [description]
        """

        cls._check_space_api_key(api_key)

    @classmethod
    def check_space_api_key_and_user(cls, api_key: str = Depends(space_api_key_header),
                                     user_id: str = Depends(space_header_api_user_header)) -> None:
        """Method to check the space api key in the request header. Also check if a user was provided/

        :param api_key: [description], defaults to Depends(oauth2_space_header_scheme)
        :type api_key: str, optional
        :raises UnauthorizedException: [description]
        """

        cls._check_space_api_key(api_key)

        # if a user was passed in the header, we check that the user exists and authenticate him
        if user_id:
            AuthService.authenticate(user_id)

    @classmethod
    def _check_space_api_key(cls, api_key: str) -> None:
        """Method to check the space api key retrieved from the header
        """

        is_authorized = SpaceService.get_instance().check_api_key(api_key)
        if not is_authorized:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.value,
                unique_code=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.name
            )
