from datetime import datetime, timedelta
from typing import TypedDict

from fastapi import Depends
from jwt import decode, encode

from ..core.utils.settings import Settings
from .invalid_token_exception import InvalidTokenException
from .oauth2_user_cookie_scheme import oauth2_user_cookie_scheme

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 3        # 3 days


class JWTData(TypedDict):
    sub: str
    exp: datetime


class JWTService:
    """Service to manage the JWT, (check, create)
    """

    _secret: str = None

    @classmethod
    def create_jwt(cls, user_uri: str) -> str:
        # calculate the expiration date
        expire = datetime.utcnow() + timedelta(seconds=cls.get_token_duration_in_seconds())

        data: JWTData = {"sub": user_uri, "exp": expire}

        encoded_jwt = encode(data, cls._get_secret(), algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def check_user_access_token(cls, token: str = Depends(oauth2_user_cookie_scheme)) -> str:
        """Check the jwt and return user uri if token is valid

        :param token: [description], defaults to Depends(oauth2_user_cookie_scheme)
        :type token: str, optional
        :return: user jwt
        :rtype: str
        """
        payload: JWTData = decode(token, cls._get_secret(),
                                  algorithms=[ALGORITHM])
        uri: str = payload.get("sub")
        if uri is None:
            raise InvalidTokenException()

        return uri

    @classmethod
    def get_token_duration_in_seconds(cls) -> int:
        return ACCESS_TOKEN_EXPIRE_SECONDS

    @classmethod
    def _get_secret(cls) -> str:
        if cls._secret is None:
            cls._secret = Settings.retrieve().data.get("secret_key")

        return cls._secret
