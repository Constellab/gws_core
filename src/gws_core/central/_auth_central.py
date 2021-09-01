# Core GWS app module
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from ..core.exception.exceptions import UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from ._oauth2_central_header_scheme import oauth2_central_header_scheme
from .central_service import CentralService


class AuthCentral:

    @classmethod
    def check_central_api_key(cls, api_key: str = Depends(oauth2_central_header_scheme)):
        """Method to check the central api key in the request header

        :param api_key: [description], defaults to Depends(oauth2_central_header_scheme)
        :type api_key: str, optional
        :raises UnauthorizedException: [description]
        """

        is_authorized = CentralService.check_api_key(api_key)
        if not is_authorized:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.value,
                unique_code=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.name
            )
