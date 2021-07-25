# Core GWS app module
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends
from fastapi.responses import JSONResponse

from ...dto.user_dto import UserData
from ...exception.gws_exceptions import GWSException
from ...exception.unauthorized_exception import UnauthorizedException
from ...settings import Settings
from ...user import User
from ._oauth2_central_header_scheme import oauth2_central_header_scheme

settings = Settings.retrieve()
SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*3        # 3 days
COOKIE_MAX_AGE_SECONDS = 60*60*24*3     # 3 days


def check_central_api_key(api_key: str = Depends(oauth2_central_header_scheme)):
    from ...service.central_service import CentralService
    is_authorized = CentralService.check_api_key(api_key)
    if not is_authorized:
        raise UnauthorizedException(
            detail=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.value,
            unique_code=GWSException.WRONG_CREDENTIALS_INVALID_API_KEY.name
        )

def get_user(user_uri: str) -> UserData:
    try:
        db_user = User.get(User.uri == user_uri)
        return UserData(
            uri=db_user.uri,
            is_admin=db_user.is_admin,
            is_active=db_user.is_active
        )
    except:
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def generate_user_access_token(uri: str) -> JSONResponse:
    user: UserData = get_user(uri)
    if not user:
        raise UnauthorizedException(
            detail=GWSException.WRONG_CREDENTIALS_USER_NOT_FOUND.value,
            unique_code=GWSException.WRONG_CREDENTIALS_USER_NOT_FOUND.name,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not (user.is_active):
        raise UnauthorizedException(
            detail=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.value,
            unique_code=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.name,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.uri,
        },
        expires_delta=access_token_expires
    )

    content = {"access_token": access_token, "token_type": "bearer"}
    response = JSONResponse(content=content)
    response.set_cookie(
        "Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=COOKIE_MAX_AGE_SECONDS,
        expires=COOKIE_MAX_AGE_SECONDS,
    )

    return response
