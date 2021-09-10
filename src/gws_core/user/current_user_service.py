import re
from typing import Union

from starlette_context import context

from ..core.exception.exceptions import (BadRequestException,
                                         UnauthorizedException)
from ..core.utils.http_helper import HTTPHelper
from .user import User


class CurrentUserService:
    """Class to manage the current connected user

    Use to set and get the user in a session
    """

    _console_data = {"user": None}

    @classmethod
    def get_and_check_current_user(cls) -> User:
        """
        Get the user in the current session, throw an exception if the user does not exists
        """

        user: User = cls.get_current_user()

        if user is None or not user.is_authenticated:
            raise UnauthorizedException("User not authenticated")

        return user

    @classmethod
    def get_current_user(cls) -> Union[User, None]:
        """
        Get the user in the current session, return none if the user is not authenticated
        """
        if HTTPHelper.is_http_context() and "user" in context.data:
            return context.data["user"]

        if "user" in cls._console_data:
            return cls._console_data["user"]

        return None

    @classmethod
    def set_current_user(cls, user: User) -> None:
        """
        Set the user in the current session
        """

        if user is None:
            try:
                # is http context
                context.data["user"] = None
            except:
                # is console context
                cls._console_data["user"] = None
        else:
            if isinstance(user, dict):
                try:
                    user = User.get(User.uri == user.uri)
                except Exception as err:
                    raise BadRequestException("Invalid current user") from err

            if not isinstance(user, User):
                raise BadRequestException("Invalid current user")

            if not user.is_active:
                raise UnauthorizedException("User not activate")

            try:
                # is http contexts
                context.data["user"] = user
            except Exception as _:
                # is console context
                cls._console_data["user"] = user

    @classmethod
    def check_is_sysuser(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: sysuser required")

        if not user.is_sysuser:
            raise UnauthorizedException(detail="Unauthorized: sysuser required")

    @classmethod
    def check_is_owner(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: owner required")

        if not user.is_owner:
            raise UnauthorizedException(detail="Unauthorized: owner required")

    @classmethod
    def check_is_admin(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: admin required")

        if not user.is_admin:
            raise UnauthorizedException(detail="Unauthorized: admin required")
