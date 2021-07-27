from starlette_context import context

from ..core.exception import BadRequestException, UnauthorizedException
from .user import User


class CurrentUserService:
    """Class to manage the current connected user

    Use to set and get the user in a session
    """

    _console_data = {"user": None}

    @classmethod
    def get_current_user(cls) -> User:
        """
        Get the user in the current session
        """

        try:
            user = context.data["user"]
        except Exception as _:
            # is console context
            try:
                user = cls._console_data["user"]
            except Exception as err:
                raise BadRequestException(
                    "No HTTP nor Console user authenticated") from err
        if user is None:
            raise BadRequestException("No HTTP nor Console user authenticated")
        return user

    @classmethod
    def set_current_user(cls, user: User):
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
