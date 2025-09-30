

from enum import Enum

from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.user.auth_context import AuthContextBase, AuthContextUser
from starlette_context import context

from ..core.exception.exceptions import (BadRequestException,
                                         UnauthorizedException)
from ..core.utils.http_helper import HTTPHelper
from .user import User


class CurrentUserContext(Enum):
    NORMAL = 'NORMAL'
    # set to app context when the code is executed in app
    APP = 'APP'


class CurrentUserService:
    """Class to manage the current connected user

    Use to set and get the user in a session
    """

    _no_context_user: User = None
    _no_http_context_auth: AuthContextBase = None

    _run_context: CurrentUserContext = CurrentUserContext.NORMAL

    @classmethod
    def get_and_check_current_user(cls) -> User:
        """
        Get the user in the current session, throw an exception if the user does not exists
        """

        user: User = cls.get_current_user()

        if user is None:
            if cls._run_context == CurrentUserContext.APP:
                raise UnauthorizedException(
                    "User not authenticated in app context. " +
                    "If this action was trigger in a `on_click`, `on_change`, in a st.dialog or similar, " +
                    "please use the `StreamlitAuthenticateUser` class in streamlit app to authenticate the user")
            else:
                raise UnauthorizedException("User not authenticated")

        return user

    @classmethod
    def get_auth_context(cls) -> AuthContextBase | None:
        """
        Get the auth context in the current session, return none if not exists
        """
        if HTTPHelper.is_http_context():
            return context.data.get("auth_context")
        elif cls._no_http_context_auth is not None:
            return cls._no_http_context_auth

        return None

    @classmethod
    def get_current_user(cls) -> User | None:
        """
        Get the user in the current session, return none if the user is not authenticated
        """
        auth_context = cls.get_auth_context()
        if auth_context is not None:
            return auth_context.get_user()

        return None

    @classmethod
    def user_is_authenticated(cls) -> bool:
        """
        Check if the user is authenticated
        """
        return cls.get_current_user() is not None

    @classmethod
    def set_auth_user(cls, user: User) -> AuthContextUser:
        """
        Set the user in the current session
        """

        if not isinstance(user, User):
            raise BadRequestException("Invalid current user")

        auth_context = AuthContextUser(user)
        cls.set_auth_context(auth_context)
        return auth_context

    @classmethod
    def set_auth_context(cls, auth_context: AuthContextBase) -> None:
        """
        Set the auth context in the current session
        """

        if not isinstance(auth_context, AuthContextBase):
            raise BadRequestException("Invalid auth context")

        if HTTPHelper.is_http_context():
            # is http contexts
            context.data["auth_context"] = auth_context
        else:
            cls._no_http_context_auth = auth_context
            cls._no_context_user = auth_context.get_user()

    @classmethod
    def clear_auth_context(cls) -> None:
        """
        Clear the auth context in the current session
        """
        if HTTPHelper.is_http_context():
            # is http contexts
            context.data["auth_context"] = None
        else:
            cls._no_http_context_auth = None
            cls._no_context_user = None

    @classmethod
    def set_current_user_from_share_auth(cls) -> None:
        """
        Set the user in the current session from a share authentication
        """

        if not HTTPHelper.is_http_context():
            # is http contexts
            raise BadRequestException("Cannot set share user in non http context")
        system_user = User.get_and_check_sysuser()
        context.data["auth_context"] = AuthContextBase('share', system_user)

    @classmethod
    def check_is_sysuser(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: sysuser required")

        if not user.is_sysuser:
            raise UnauthorizedException(detail="Unauthorized: sysuser required")

    @classmethod
    def check_is_admin(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: admin required")

        if not user.is_admin:
            raise UnauthorizedException(detail="Unauthorized: admin required")

    @classmethod
    def get_current_user_theme(cls) -> FrontTheme:
        user = CurrentUserService.get_current_user()
        if user is None:
            return FrontService.get_light_theme()

        return FrontService.get_dark_theme() if user.has_dark_theme() else FrontService.get_light_theme()

    @classmethod
    def set_app_context(cls):
        cls._run_context = CurrentUserContext.APP

    @classmethod
    def is_app_context(cls) -> bool:
        return cls._run_context == CurrentUserContext.APP


class AuthenticateUser:
    """ Class to authenticate a user in a context.
    """

    user: User

    was_already_authenticated: bool = False

    def __init__(self, user: User) -> None:
        self.user = user

    def __enter__(self):
        if CurrentUserService.get_current_user() is None:
            CurrentUserService.set_auth_user(self.user)
        else:
            self.was_already_authenticated = True
        # Code to set up and acquire resources
        return self  # You can return an object that you want to use in the with block

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.was_already_authenticated:
            CurrentUserService.clear_auth_context()

        # raise the exception if exists
        if exc_value:
            raise exc_value

    @staticmethod
    def system_user() -> 'AuthenticateUser':
        """ Authenticate the system user in a context.
        """
        return AuthenticateUser(User.get_and_check_sysuser())
