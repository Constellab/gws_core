from typing import Optional

from fastapi.requests import Request
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param

from gws_core.space.space_service import SpaceService

from ..core.exception.exceptions import BadRequestException


class SpaceApiKeyHeader(OAuth2):

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get(SpaceService.AUTH_HEADER_KEY)
        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )

        if header_scheme.lower() == SpaceService.AUTH_API_KEY_HEADER_PREFIX:
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
        return request.headers.get(SpaceService.USER_ID_HEADER_KEY)


space_header_api_user_header = SpaceAPIUserHeader()
