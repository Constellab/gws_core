from enum import Enum

from fastapi import Request

from gws_core.apps.app_process import AppProcess
from gws_core.apps.apps_manager import AppsManager
from gws_core.core.exception.exceptions.forbidden_exception import ForbiddenException
from gws_core.core.utils.settings import Settings
from gws_core.share.share_link_service import ShareLinkService
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
    # Header carrying, depending on the request: the app-scoped token (app -> lab API calls) or the
    # single-use space access code (share-link / space open). The legacy name is kept for wire
    # compatibility; the value is NOT a general user/session token. See APP_AUTH_OAUTH_REDESIGN.md
    # (the planned split into gws_app_token / gws_space_access_code). Also mirrored as a literal in
    # front_service.py's space-open URL and in the gws_core-free app bases (they cannot import this).
    USER_ACCESS_TOKEN_HEADER = "gws_user_access_token"
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
        user_access_token = request.headers.get(cls.USER_ACCESS_TOKEN_HEADER)

        if not app_id or not user_access_token:
            return None

        user: User | None = None

        if (
            app_id == AppProcess.DEV_MODE_APP_ID
            and user_access_token == AppProcess.DEV_MODE_USER_ACCESS_TOKEN_KEY
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
            # The launching user's token is an app-scoped JWT (typ:app, bound to app_id), minted by
            # the gws_code exchange. The in-app sentinel tokens (system user, dev) are opaque and
            # resolved via the in-memory map. Try the map first, then validate as an app token.
            user_id = AppsManager.user_has_access_to_app(app_id, user_access_token)

            if not user_id:
                user_id = cls._user_id_from_app_token(user_access_token, app_id)

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
    def _user_id_from_app_token(cls, user_access_token: str, app_id: str) -> str | None:
        """Resolve the user id from an app-scoped token, or None if it is not valid for this app.

        The launching user's app token is the app-scoped JWT minted by the gws_code exchange
        (AppsManager.exchange_app_code): it carries ``typ == "app"`` and an ``app_id`` claim, so it
        authenticates only as an app credential and only for the app it was minted for. Carried in
        the ``gws_user_access_token`` header; JWTService expects the ``Bearer `` scheme, so add it
        if absent.
        """
        token = (
            user_access_token
            if user_access_token.startswith(JWTService.AUTH_SCHEME)
            else JWTService.AUTH_SCHEME + user_access_token
        )
        try:
            return JWTService.check_app_access_token(token, app_id)
        except Exception:
            return None

    @classmethod
    def _auth_share_link(cls, request: Request) -> AuthContextShareLink | None:
        token = request.headers.get("Authorization")
        if not token or not token.startswith(cls.SHARE_LINK_AUTH_SCHEME):
            return None

        share_link_token = token[len(cls.SHARE_LINK_AUTH_SCHEME) :]

        # For a SPACE link the caller sends the single-use space access code in the
        # USER_ACCESS_TOKEN_HEADER (legacy header name; the value is a space access code, not a
        # user/session token). PUBLIC links ignore it.
        space_access_code = request.headers.get(cls.USER_ACCESS_TOKEN_HEADER)
        return cls.auth_share_link_from_token(share_link_token, space_access_code)

    @classmethod
    def auth_share_link_from_token(
        cls, share_link_token: str, space_access_code: str | None = None
    ) -> AuthContextShareLink:
        share_link = ShareLinkService.find_by_token_and_check_validity(share_link_token)

        user: User
        # SPACE link: authenticated by a single-use space access code (NOT a user/session token),
        # minted by ShareLink.generate_space_access_code. The ShareLink entity owns consuming it
        # and confirming it was minted for this exact link.
        if share_link.link_type == ShareLinkType.SPACE:
            if not space_access_code:
                raise ForbiddenException("This link requires authentication")

            user_id = share_link.check_space_access_code(space_access_code)
            user = cls._get_and_check_user(user_id, allow_inactive=True)
        else:
            # PUBLIC link: normally authenticates the visitor as the system user (so a public
            # resource preview can call the API). Refuse this for an app that requires
            # authentication — it would silently elevate any visitor to the system user and bypass
            # the app's auth. Such apps must be opened via a SPACE link or the launcher gateway.
            # (New PUBLIC links on these apps are also blocked at creation in
            # ShareLinkService.generate_share_link; this guards links created before that check.)
            if ShareLinkService.resource_is_authenticated_app(
                share_link.entity_type, share_link.entity_id
            ):
                raise ForbiddenException(
                    "This app requires authentication and cannot be opened through a public link."
                )
            user = User.get_and_check_sysuser()

        auth_context = AuthContextShareLink(share_link=share_link, user=user)
        CurrentUserService.set_auth_context(auth_context)
        return auth_context

    @classmethod
    def check_unique_code(cls, unique_code: str, allow_inactive: bool = False) -> AuthContextUser:
        """Consume a one-time code and authenticate the user it was minted for.

        :param unique_code: the single-use code (consumed here)
        :param allow_inactive: when True, authenticate a user that exists but is not active. Used
            by the app launcher gateway: a user can reach an app from the space without lab access
            (exists in DB but cannot log in). Defaults to False so login-style callers stay strict.
        """
        try:
            code_obj: CodeObject = UniqueCodeService.check_code(unique_code)

            user = cls._get_and_check_user(code_obj.user_id, allow_inactive=allow_inactive)
            return CurrentUserService.set_auth_user(user)
        except Exception as e:
            raise InvalidUniqueCodeException() from e

    @classmethod
    def get_token_from_request(cls, request: Request) -> str | None:
        header_authorization: str | None = request.headers.get("Authorization")
        cookie_authorization: str | None = request.cookies.get("Authorization")

        return header_authorization or cookie_authorization

    @classmethod
    def get_and_check_token_from_request(cls, request: Request) -> str:
        token: str | None = cls.get_token_from_request(request)
        if not token:
            raise InvalidTokenException()
        return token

    @classmethod
    def authenticate_from_token(cls, token: str) -> AuthContextUser:
        try:
            user_id: str = JWTService.check_user_access_token(token)
            return cls.authenticate_user(user_id)

        except Exception as e:
            raise InvalidTokenException() from e

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
