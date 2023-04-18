# Core GWS app module
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi.requests import Request
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from gws_core.space.space_service import SpaceService

from ..core.exception.exceptions import BadRequestException


class SpaceApiKeyHeader(OAuth2):

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get(SpaceService.api_key_header_key)
        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )

        if header_scheme.lower() == SpaceService.api_key_header_prefix:
            authorization = True
            param = header_param
        else:
            authorization = False

        if not authorization:
            if self.auto_error:
                raise BadRequestException("Not authorized. Invalid request.")
            else:
                return None

        return param


space_api_key_header = SpaceApiKeyHeader()


class SpaceAPIUserHeader(OAuth2):

    async def __call__(self, request: Request) -> Optional[str]:
        return request.headers.get(SpaceService.user_id_header_key)


space_header_api_user_header = SpaceAPIUserHeader()
