# Core GWS app module
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from gws_core.user.auth_service import AuthService

from ..core.exception.exceptions import UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from ._oauth2_central_header_scheme import (centra_api_key_header,
                                            central_header_api_user_header)
from .central_service import CentralService


class AuthCentral:

    @classmethod
    def check_central_api_key(cls, api_key: str = Depends(centra_api_key_header)) -> None:
        """Method to check the central api key in the request header

        :param api_key: [description], defaults to Depends(oauth2_central_header_scheme)
        :type api_key: str, optional
        :raises UnauthorizedException: [description]
        """

        cls._check_central_api_key(api_key)

    @classmethod
    def check_central_api_key_and_user(cls, api_key: str = Depends(centra_api_key_header),
                                       user_id: str = Depends(central_header_api_user_header)) -> None:
        """Method to check the central api key in the request header. Also check if a user was provided/

        :param api_key: [description], defaults to Depends(oauth2_central_header_scheme)
        :type api_key: str, optional
        :raises UnauthorizedException: [description]
        """

        cls._check_central_api_key(api_key)

        # if a user was passed in the header, we check that the user exists and authenticate him
        if user_id:
            AuthService.authenticate(user_id)

    @classmethod
    def _check_central_api_key(cls, api_key: str) -> None:
        """Method to check the central api key retrieved from the header
        """

        is_authorized = CentralService.check_api_key(api_key)
        if not is_authorized:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.value,
                unique_code=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.name
            )
