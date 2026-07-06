from datetime import datetime, timedelta
from typing import Any

from jwt import decode, encode
from typing_extensions import TypedDict

from gws_core.core.utils.date_helper import DateHelper

from ..core.utils.settings import Settings
from .user_exception import InvalidTokenException


class JWTData(TypedDict):
    sub: str
    exp: datetime


# JWT "typ" claim marking an app-scoped access token (see APP_AUTH_OAUTH_REDESIGN.md). An app token
# authenticates a user only for a specific app's API calls (AuthorizationMode.APP -> AuthContextApp)
# and is rejected on normal user routes. A general lab-session JWT carries no "typ" claim.
APP_TOKEN_TYPE = "app"
# Claim holding the app resource model id an app token is scoped to.
APP_ID_CLAIM = "app_id"


class JWTService:
    """Service to manage the JWT, (check, create)"""

    AUTH_SCHEME = "Bearer "
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 2  # 2 days

    _secret: str | None = None

    @classmethod
    def create_jwt(cls, user_id: str) -> str:
        # calculate the expiration date
        expire = DateHelper.now_utc() + timedelta(seconds=cls.get_token_duration_in_seconds())

        data: dict[str, Any] = {"sub": user_id, "exp": expire}

        encoded_jwt = encode(data, cls._get_secret(), algorithm=cls.ALGORITHM)
        return JWTService.AUTH_SCHEME + encoded_jwt

    @classmethod
    def create_app_jwt(cls, user_id: str, app_id: str) -> str:
        """Create an app-scoped access token for a user, bound to a single app.

        The token carries ``typ = "app"`` and the ``app_id`` claim so it can be authenticated only
        as an app credential (AuthorizationMode.APP -> AuthContextApp) and rejected on normal user
        routes. See APP_AUTH_OAUTH_REDESIGN.md.
        """
        expire = DateHelper.now_utc() + timedelta(seconds=cls.get_token_duration_in_seconds())

        data: dict[str, Any] = {
            "sub": user_id,
            "exp": expire,
            "typ": APP_TOKEN_TYPE,
            APP_ID_CLAIM: app_id,
        }

        encoded_jwt = encode(data, cls._get_secret(), algorithm=cls.ALGORITHM)
        return JWTService.AUTH_SCHEME + encoded_jwt

    @classmethod
    def _decode(cls, token: str) -> dict:
        """Strip the scheme prefix and decode/verify the JWT payload (raises on invalid)."""
        if not token or not token.startswith(cls.AUTH_SCHEME):
            raise InvalidTokenException()

        token = token[len(cls.AUTH_SCHEME) :]
        return decode(token, cls._get_secret(), algorithms=[cls.ALGORITHM])

    @classmethod
    def check_user_access_token(cls, token: str) -> str:
        """Check a **general user session** JWT and return the user id if valid.

        Rejects app-scoped tokens (``typ == "app"``): those authenticate only as an app credential
        and must not grant access to normal user routes.

        :param token: the ``Bearer <jwt>`` token
        :return: the user id (``sub``)
        """
        payload = cls._decode(token)

        # an app-scoped token is not a user session; do not let it authenticate user routes
        if payload.get("typ") == APP_TOKEN_TYPE:
            raise InvalidTokenException()

        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidTokenException()

        return user_id

    @classmethod
    def check_app_access_token(cls, token: str, app_id: str) -> str:
        """Check an app-scoped access token for a specific app and return the user id if valid.

        Verifies the token is an app token (``typ == "app"``) and that its ``app_id`` claim matches
        the calling app, so a token minted for app A cannot be replayed on app B.

        :param token: the ``Bearer <jwt>`` token (app-scoped)
        :param app_id: the app resource model id the token must be bound to
        :return: the user id (``sub``)
        """
        payload = cls._decode(token)

        if payload.get("typ") != APP_TOKEN_TYPE:
            raise InvalidTokenException()
        if payload.get(APP_ID_CLAIM) != app_id:
            raise InvalidTokenException()

        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidTokenException()

        return user_id

    @classmethod
    def get_token_duration_in_seconds(cls) -> int:
        return cls.ACCESS_TOKEN_EXPIRE_SECONDS

    @classmethod
    def get_token_duration_in_milliseconds(cls) -> int:
        return cls.get_token_duration_in_seconds() * 1000

    @classmethod
    def _get_secret(cls) -> str:
        if cls._secret is None:
            cls._secret = Settings.get_instance().data.get("secret_key")

        assert cls._secret is not None, "secret_key is not configured in the settings"
        return cls._secret
