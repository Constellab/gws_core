from enum import Enum

from fastapi import Request
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.apps_manager import AppsManager
from gws_core.core.exception.exceptions.forbidden_exception import ForbiddenException
from gws_core.core.utils.settings import Settings
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.share_link_space_access import ShareLinkSpaceAccessService
from gws_core.share.shared_dto import ShareLinkType
from gws_core.user.auth_context import (
    AuthContext,
    AuthContextApp,
    AuthContextShareLink,
    AuthContextUser,
)

from ..core.exception.exceptions import UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from .current_user_service import CurrentUserService
from .jwt_service import JWTService
from .unique_code_service import CodeObject, InvalidUniqueCodeException, UniqueCodeService
from .user import User
from .user_exception import InvalidTokenException


class AuthorizationMode(Enum):
    USER = "USER"
    APP = "APP"
    SHARE_LINK = "SHARE_LINK"


class AuthorizationService:
    """Service for handling user authorization when accessing resources"""

    SHARE_LINK_AUTH_SCHEME = "ShareToken "
    # Flag to allow connections from dev mode apps
    allow_dev_app_connections: bool = False

    @classmethod
    def check_user_access_token(cls, request: Request) -> AuthContext:
        token = cls.get_and_check_token_from_request(request)

        return cls.authenticate_from_token(token)

    @classmethod
    def check_user_access_token_or_app(cls, request: Request) -> AuthContext:
        """Method to allow authentication from :
        - normal token
        - user access token for streamlit app

        If user access token is provided, only this method is used
        even if there is a normal token
        """

        return cls.check_authorization(request, [AuthorizationMode.APP, AuthorizationMode.USER])

    @classmethod
    def check_user_access_token_or_share_link(cls, request: Request) -> AuthContext:
        """Method to allow authentication from :
        - normal token
        - share link token

        If share link token is provided, only this method is used
        even if there is a normal token
        """

        return cls.check_authorization(
            request, [AuthorizationMode.SHARE_LINK, AuthorizationMode.USER]
        )

    @classmethod
    def check_authorization(cls, request: Request, modes: list[AuthorizationMode]) -> AuthContext:
        """Method to check the authorization based on the provided modes

        The modes are checked in the order they are provided
        """

        if AuthorizationMode.SHARE_LINK in modes:
            share_link_auth = cls._auth_share_link(request)
            if share_link_auth:
                return share_link_auth

        if AuthorizationMode.APP in modes:
            app_auth = cls._auth_app(request)
            if app_auth:
                return app_auth

        if AuthorizationMode.USER in modes:
            return cls.check_user_access_token(request)

        raise UnauthorizedException("No valid authentication method found")

    @classmethod
    def check_share_link(cls, request: Request) -> AuthContextShareLink:
        """Method to get and check the share token from the request

        If the header gws_user_access_token is present, it will be used to check the the access for the user
        """

        auth_context = cls._auth_share_link(request)
        if not auth_context:
            raise ForbiddenException("No share token provided")

        return auth_context

    @classmethod
    def _auth_app(cls, request: Request) -> AuthContextApp | None:
        app_id = request.headers.get("gws_app_id")
        user_access_token = request.headers.get("gws_user_access_token")

        if not app_id or not user_access_token:
            return None

        user: User = None

        if (
            app_id == AppInstance.DEV_MODE_APP_ID
            and user_access_token == AppInstance.DEV_MODE_USER_ACCESS_TOKEN_KEY
        ):
            if Settings.is_prod_mode():
                raise UnauthorizedException(
                    detail="Dev mode app cannot be used in production",
                    unique_code=GWSException.INVALID_APP_TOKEN.name,
                )
            if not cls.allow_dev_app_connections:
                raise UnauthorizedException(
                    detail="Dev mode app connections are not allowed, please start the dev server with the option --allow-dev-app-connections",
                    unique_code=GWSException.INVALID_APP_TOKEN.name,
                )
            user = User.get_and_check_sysuser()

        else:
            user_id = AppsManager.user_has_access_to_app(app_id, user_access_token)

            if not user_id:
                raise UnauthorizedException(
                    detail=GWSException.INVALID_APP_TOKEN.value,
                    unique_code=GWSException.INVALID_APP_TOKEN.name,
                )

            user = cls._get_and_check_user(user_id)

        auth_context = AuthContextApp(app_id=app_id, user=user)
        CurrentUserService.set_auth_context(auth_context)
        return auth_context

    @classmethod
    def _auth_share_link(cls, request: Request) -> AuthContextShareLink | None:
        token = request.headers.get("Authorization")
        if not token or not token.startswith(cls.SHARE_LINK_AUTH_SCHEME):
            return None

        if not token or not token.startswith(cls.SHARE_LINK_AUTH_SCHEME):
            raise InvalidTokenException()

        share_link_token = token[len(cls.SHARE_LINK_AUTH_SCHEME) :]

        user_access_token = request.headers.get("gws_user_access_token")
        return cls.auth_share_link_from_token(share_link_token, user_access_token)

    @classmethod
    def auth_share_link_from_token(
        cls, share_link_token: str, user_access_token: str | None = None
    ) -> AuthContextShareLink:
        share_link = ShareLinkService.find_by_token_and_check_validity(share_link_token)

        user: User
        # if the link is a space access link, check if the user access token is valid
        if share_link.link_type == ShareLinkType.SPACE:
            if not user_access_token:
                raise ForbiddenException("This link requires authentication")
            space_access_info = ShareLinkSpaceAccessService.find_by_token_and_check_validity(
                user_access_token, share_link.id
            )

            user = cls._get_and_check_user(space_access_info.user_id, allow_inactive=True)
        else:
            user = User.get_and_check_sysuser()

        auth_context = AuthContextShareLink(share_link=share_link, user=user)
        CurrentUserService.set_auth_context(auth_context)
        return auth_context

    @classmethod
    def check_unique_code(cls, unique_code: str) -> AuthContextUser:
        """Use link the the token to check access for a unique code generated. return the object associated with the code"""
        try:
            code_obj: CodeObject = UniqueCodeService.check_code(unique_code)

            return cls.authenticate_user(code_obj.user_id)
        except Exception:
            raise InvalidUniqueCodeException()

    @classmethod
    def get_token_from_request(cls, request: Request) -> str | None:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")

        return header_authorization or cookie_authorization

    @classmethod
    def get_and_check_token_from_request(cls, request: Request) -> str:
        token: str = cls.get_token_from_request(request)
        if not token:
            raise InvalidTokenException()
        return token

    @classmethod
    def authenticate_from_token(cls, token: str) -> AuthContext:
        try:
            user_id: str = JWTService.check_user_access_token(token)
            return cls.authenticate_user(user_id)

        except Exception:
            raise InvalidTokenException()

    @classmethod
    def authenticate_user(cls, user_id: str) -> AuthContextUser:
        """
        Authenticate a user. Return the DB user if ok, throw an exception if not ok

        :param id: The id of the user to authenticate
        :type id: `str`
        """
        user: User = cls._get_and_check_user(user_id)

        # Set the user in the context
        return CurrentUserService.set_auth_user(user)

    @classmethod
    def _get_and_check_user(cls, user_id: str, allow_inactive: bool = False) -> User:
        user: User = User.get_by_id_and_check(user_id)

        if not user.is_active and not allow_inactive:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.value,
                unique_code=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.name,
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
