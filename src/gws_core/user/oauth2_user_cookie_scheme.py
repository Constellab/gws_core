
from typing import Optional

from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.requests import Request
from fastapi.security import OAuth2

from .user_exception import InvalidTokenException


class OAuth2UserTokenBearerCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

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


oauth2_user_cookie_scheme = OAuth2UserTokenBearerCookie(
    tokenUrl="/user/login/{id}/{token}")
