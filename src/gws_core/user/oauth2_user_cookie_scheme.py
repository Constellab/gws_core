# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi.requests import Request
from fastapi.security import OAuth2

from .user_exception import InvalidTokenException


class OAuth2UserTokenBearerCookie(OAuth2):

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")

        authorization = header_authorization or cookie_authorization

        if not authorization:
            if self.auto_error:
                raise InvalidTokenException()
            else:
                return None

        return authorization


oauth2_user_cookie_scheme = OAuth2UserTokenBearerCookie()
