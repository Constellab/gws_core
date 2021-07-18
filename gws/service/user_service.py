# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Coroutine, Union
from starlette.responses import JSONResponse
from starlette_context import context

from ..dto.credentials_dto import CredentialsDTO
from ..exception.wrong_credentials_exception import WrongCredentialsException
from ..http import HTTPInternalServerError, HTTPUnauthorized
from ..logger import Error
from ..activity import Activity
from ..user import User
from ..query import Paginator
from .._app._central_app._auth_central import generate_user_access_token
from .base_service import BaseService
from .central_service import CentralService

class UserService(BaseService):

    _console_data = {"user": None}

    # -- A --

    @classmethod
    def activate_user(cls, uri) -> User:
        return cls.set_user_status(uri, {"is_active": True})

    # -- C --

    @classmethod
    def create_user(cls, data: dict) -> User:
        group = data.get('group', 'user')
        if group == "sysuser":
            raise Error("Central", "create_user", "Cannot create sysuser")
        u = User.get_by_uri(data['uri'])
        if not u:
            user = User(
                uri=data['uri'],
                email=data['email'],
                group=group,
                is_active=data.get('is_active', True),
                data={
                    "first_name": data['first_name'],
                    "last_name": data['last_name'],
                }
            )
            if user.save():
                return User.get_by_uri(user.uri)
            else:
                raise Error("Central", "create_user",
                            "Cannot create the user")
        else:
            raise Error("Central", "create_user",
                        "The user already exists")

    # -- D --

    @classmethod
    def deactivate_user(cls, uri) -> User:
        return cls.set_user_status(uri, {"is_active": False})

    # -- F --

    @classmethod
    def fecth_activity_list(cls,
                            user_uri: str = None,
                            activity_type: str = None,
                            page: int = 1,
                            number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, dict]:

        query = Activity.select().order_by(Activity.creation_datetime.desc())
        if user_uri:
            query = query.join(User).where(User.uri == user_uri)
        if activity_type:
            query = query.where(Activity.activity_type == activity_type.upper())
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator

    @classmethod
    def fetch_user(cls, uri: str) -> User:
        return User.get_by_uri(uri)

    @classmethod
    def fetch_user_list(cls,
                        page: int = 1,
                        number_of_items_per_page: int = 20,
                        as_json=False) -> Union[Paginator, dict]:

        query = User.select().order_by(User.creation_datetime.desc())
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator

    # -- G --

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
                raise Error("UserService", "get_current_user", "No HTTP nor Console user authenticated") from err
        if user is None:
            raise Error("UserService", "get_current_user", "No HTTP nor Console user authenticated")
        return user

    @classmethod
    def get_user_by_uri(cls, uri: str) -> User:
        return User.get_by_uri(uri)

    @classmethod
    def get_user_by_email(cls, email: str) -> User:
        return User.get_by_email(email)

    # -- S --

    @classmethod
    def set_user_status(cls, uri, data) -> User:
        user = User.get_by_uri(uri)
        if user is None:
            raise Error("Central", "set_user_status", "User not found")
        if "is_active" in data:
            user.is_active = data["is_active"]
        if "group" in data:
            user.group = data["group"]
        if not user.save():
            raise Error("Central", "set_user_status", "Cannot save the user")
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
                    raise HTTPInternalServerError(detail="Invalid current user") from err

            if not isinstance(user, User):
                raise HTTPInternalServerError(detail="Invalid current user")

            if not user.is_active:
                raise HTTPUnauthorized(detail="Not authorized")

            try:
                # is http contexts
                context.data["user"] = user
            except Exception as _:
                # is console context
                cls._console_data["user"] = user

    @classmethod
    def get_all_users(cls):
        return list(User.select())

    @classmethod
    async def login(cls, credentials: CredentialsDTO) -> Coroutine[Any, Any, JSONResponse]:

        # Check if user exist in the lab
        user: User = cls.get_user_by_email(credentials.email)
        if user is None:
            raise WrongCredentialsException()

        # Check the user credentials
        credentials_valid: bool = CentralService.check_credentials(credentials)
        if not credentials_valid:
            raise WrongCredentialsException()

        return await generate_user_access_token(user.uri)
