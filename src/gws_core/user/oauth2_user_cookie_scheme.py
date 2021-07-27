
from typing import Optional

from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.requests import Request
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette import status

from ..core.exception import BaseHTTPException, GWSException


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

        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param
        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param
        else:
            authorization = False

        if not authorization:
            if self.auto_error:
                raise BaseHTTPException(
                    http_status_code=status.HTTP_403_FORBIDDEN, detail=GWSException.INVALID_TOKEN.value,
                    unique_code=GWSException.INVALID_TOKEN.name)
            else:
                return None

        return param


oauth2_user_cookie_scheme = OAuth2UserTokenBearerCookie(
    tokenUrl="/user/login/{uri}/{token}")
