

from enum import Enum
from typing import Union

from starlette_context import context

from gws_core.core.service.front_service import FrontService, FrontTheme

from ..core.exception.exceptions import (BadRequestException,
                                         UnauthorizedException)
from ..core.utils.http_helper import HTTPHelper
from .user import User


class CurrentUserContext(Enum):
    NORMAL = 'NORMAL'
    # set to streamlit context when the code is executed in streamlit
    STREAMLIT = 'STREAMLIT'


class CurrentUserService:
    """Class to manage the current connected user

    Use to set and get the user in a session
    """

    _no_context_user: User = None

    _run_context: CurrentUserContext = CurrentUserContext.NORMAL

    @classmethod
    def get_and_check_current_user(cls) -> User:
        """
        Get the user in the current session, throw an exception if the user does not exists
        """

        user: User = cls.get_current_user()

        if user is None:
            raise UnauthorizedException("User not authenticated")

        return user

    @classmethod
    def get_current_user(cls) -> Union[User, None]:
        """
        Get the user in the current session, return none if the user is not authenticated
        """
        if HTTPHelper.is_http_context():
            return context.data.get("user")
        elif cls._no_context_user is not None:
            return cls._no_context_user

        return None

    @classmethod
    def user_is_authenticated(cls) -> bool:
        """
        Check if the user is authenticated
        """
        return cls.get_current_user() is not None

    @classmethod
    def set_current_user(cls, user: User) -> None:
        """
        Set the user in the current session
        """
        # clear the user if None
        if user is None:
            if HTTPHelper.is_http_context():
                # is http context
                context.data["user"] = None
            else:
                cls._no_context_user = None

            return

        if not isinstance(user, User):
            raise BadRequestException("Invalid current user")

        if HTTPHelper.is_http_context():
            # is http contexts
            context.data["user"] = user
        else:
            cls._no_context_user = user

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
    def set_streamlit_context(cls):
        cls._run_context = CurrentUserContext.STREAMLIT

    @classmethod
    def is_streamlit_context(cls) -> bool:
        return cls._run_context == CurrentUserContext.STREAMLIT


class AuthenticateUser:
    """ Context to support with statement to catch exceptions and convert
    them to S3ServerException"""

    user: User

    was_already_authenticated: bool = False

    def __init__(self, user: User) -> None:
        self.user = user

    def __enter__(self):
        if CurrentUserService.get_current_user() is None:
            CurrentUserService.set_current_user(self.user)
        else:
            self.was_already_authenticated = True
        # Code to set up and acquire resources
        return self  # You can return an object that you want to use in the with block

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.was_already_authenticated:
            CurrentUserService.set_current_user(None)

        # raise the exception if exists
        if exc_value:
            raise exc_value
