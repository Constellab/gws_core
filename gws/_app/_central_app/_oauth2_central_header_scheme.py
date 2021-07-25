# Core GWS app module
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
import base64
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError
from pydantic import BaseModel
from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm, OAuth2
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request

from ...exception.gws_exceptions import GWSException
from ...exception.bad_request_exception import BadRequestException

class OAuth2CentralAPIKeyHeader(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        
        if header_scheme.lower() == "api-key":
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

oauth2_central_header_scheme = OAuth2CentralAPIKeyHeader(tokenUrl="/user/generate-access-token")