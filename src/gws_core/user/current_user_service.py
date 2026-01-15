from gws_core.core.service.front_service import FrontService, FrontTheme
from gws_core.user.auth_context import AuthContextBase, AuthContextUser
from gws_core.user.auth_context_loader import (
    AuthContextLoader,
)

from ..core.exception.exceptions import BadRequestException, UnauthorizedException
from ..core.utils.http_helper import HTTPHelper
from .user import User


class CurrentUserService:
    """Class to manage the current connected user with pluggable storage.

    Use to set and get the user in a session. The storage mechanism is determined
    by the initialized loader (HTTP, Streamlit, Reflex, etc.).
    """

    _auth_loader: AuthContextLoader | None = None

    @classmethod
    def initialize_loader(cls, loader: AuthContextLoader) -> None:
        """
        Initialize the auth context loader for the application.
        Must be called at app startup (Streamlit, Reflex, etc.)

        Args:
            loader: The loader implementation to use
            context: The context type (APP, REFLEX, etc.)
        """
        cls._auth_loader = loader

    @classmethod
    def _get_loader(cls) -> AuthContextLoader:
        """Get the appropriate loader for current context."""

        if cls._auth_loader is None:
            raise Exception("CurrentUserService not initialized with a loader")

        return cls._auth_loader

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the CurrentUserService has been initialized with a loader.
        """
        return cls._auth_loader is not None

    @classmethod
    def get_and_check_current_user(cls) -> User:
        """
        Get the user in the current session, throw an exception if the user does not exists
        """

        user = cls.get_current_user()

        if user is None:
            raise UnauthorizedException("User not authenticated")

        return user

    @classmethod
    def get_auth_context(cls) -> AuthContextBase | None:
        """
        Get the auth context in the current session, return none if not exists
        """
        return cls._get_loader().get()

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

        cls._get_loader().set(auth_context)

    @classmethod
    def clear_auth_context(cls) -> None:
        """
        Clear the auth context in the current session
        """
        cls._get_loader().clear()

    @classmethod
    def set_current_user_from_share_auth(cls) -> None:
        """
        Set the user in the current session from a share authentication
        """

        if not HTTPHelper.is_http_context():
            raise BadRequestException("Cannot set share user in non http context")
        system_user = User.get_and_check_sysuser()
        # Use AuthContextUser for share authentication with system user
        auth_context = AuthContextUser(system_user)
        cls._get_loader().set(auth_context)

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

        return (
            FrontService.get_dark_theme()
            if user.has_dark_theme()
            else FrontService.get_light_theme()
        )


class AuthenticateUser:
    """Class to authenticate a user in a context."""

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
    def system_user() -> "AuthenticateUser":
        """Authenticate the system user in a context."""
        return AuthenticateUser(User.get_and_check_sysuser())
