# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..core.utils.settings import Settings
from .activity import Activity
from .user import User
from .user_dto import UserDataDict
from .user_group import UserGroup


class UserService(BaseService):

    _console_data = {"user": None}

    # -- A --

    @classmethod
    def activate_user(cls, uri) -> User:
        return cls.set_user_status(uri, {"is_active": True})

    # -- C --

    @classmethod
    def create_user(cls, user: UserDataDict) -> User:

        if cls.user_exists(user["uri"]):
            raise BadRequestException("The user already exists")

        return cls._create_user(user)

    @classmethod
    def create_user_if_not_exists(cls, user: UserDataDict) -> User:
        db_user: User = cls.get_user_by_uri(user["uri"])
        if db_user is not None:
            return db_user

        return cls._create_user(user)

    @classmethod
    def _create_user(cls, data: UserDataDict) -> User:
        group: UserGroup = UserGroup.from_string(data.get('group', None), UserGroup.USER)
        if group == UserGroup.SYSUSER:
            raise BadRequestException("Cannot create sysuser")

        user = User(
            uri=data['uri'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            group=group,
            is_active=data.get('is_active', True),
            data={
            }
        )
        if user.save():
            return User.get_by_uri(user.uri)
        else:
            raise BadRequestException(
                "Cannot create the user")

    # -- D --

    @classmethod
    def deactivate_user(cls, uri) -> User:
        return cls.set_user_status(uri, {"is_active": False})

    # -- F --

    @classmethod
    def fecth_activity_list(cls,
                            user_uri: str = None,
                            activity_type: str = None,
                            page: int = 0,
                            number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, dict]:

        query = Activity.select().order_by(Activity.creation_datetime.desc())
        if user_uri:
            query = query.join(User).where(User.uri == user_uri)
        if activity_type:
            query = query.where(Activity.activity_type ==
                                activity_type.upper())
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
                        page: int = 0,
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
            raise BadRequestException("User not found")
        if "is_active" in data:
            user.is_active = data["is_active"]
        if "group" in data:
            user.group = data["group"]
        if not user.save():
            raise BadRequestException("Cannot save the user")
        return user

    @classmethod
    def get_all_users(cls):
        return list(User.select())

        # Create the admin
    def create_sysuser(cls):
        """ Create the system user """
        try:
            UserService.get_sysuser()
        except:
            user = User(
                email="admin@gencovery.com",
                first_name="sysuser",
                last_name="sysuser",
                data={},
                is_active=True,
                group=UserGroup.SYSUSER
            )
            user.save()

    # -- G --

    @classmethod
    def get_admin(cls):
        return User.get_admin()

    @classmethod
    def get_owner(cls):
        return User.get_owner()

    @classmethod
    def get_sysuser(cls):
        return User.get_sysuser()

    @classmethod
    def user_exists(cls, uri: str) -> bool:
        return cls.get_user_by_uri(uri) is not None
