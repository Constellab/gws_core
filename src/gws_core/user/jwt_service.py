from datetime import datetime, timedelta

from jwt import decode, encode
from typing_extensions import TypedDict

from ..core.utils.settings import Settings
from .user_exception import InvalidTokenException

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
    def create_jwt(cls, user_id: str) -> str:
        # calculate the expiration date
        expire = datetime.utcnow() + timedelta(seconds=cls.get_token_duration_in_seconds())

        data: JWTData = {"sub": user_id, "exp": expire}

        encoded_jwt = encode(data, cls._get_secret(), algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def check_user_access_token(cls, token: str) -> str:
        """Check the jwt and return user id if token is valid

        :param token: [description]
        :type token: str, optional
        :return: user jwt
        :rtype: str
        """
        payload: JWTData = decode(token, cls._get_secret(),
                                  algorithms=[ALGORITHM])
        id: str = payload.get("sub")
        if id is None:
            raise InvalidTokenException()

        return id

    @classmethod
    def get_token_duration_in_seconds(cls) -> int:
        return ACCESS_TOKEN_EXPIRE_SECONDS

    @classmethod
    def _get_secret(cls) -> str:
        if cls._secret is None:
            cls._secret = Settings.get_instance().data.get("secret_key")

        return cls._secret
