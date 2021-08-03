# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union

from ..core.classes.paginator import Paginator
from ..core.exception import BadRequestException
from ..core.service.base_service import BaseService
from ..core.utils.settings import Settings
from .activity import Activity
from .user import User


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
            raise BadRequestException("Cannot create sysuser")
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
                raise BadRequestException(
                    "Cannot create the user")
        else:
            raise BadRequestException(
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

    @classmethod
    def create_owner_and_sysuser(cls):
        settings_local = Settings.retrieve()

        # Create the owner
        try:
            UserService.get_owner()
        except:
            uri = settings_local.data["owner"]["uri"]
            email = settings_local.data["owner"]["email"]
            first_name = settings_local.data["owner"]["first_name"]
            last_name = settings_local.data["owner"]["last_name"]
            u = User(
                uri=uri if uri else None,
                email=email,
                data={"first_name": first_name, "last_name": last_name},
                is_active=True,
                group=User.OWNER_GROUP
            )
            u.save()

        # Create the admin
        try:
            UserService.get_sysuser()
        except:
            u = User(
                email="admin@gencovery.com",
                data={"first_name": "sysuser", "last_name": ""},
                is_active=True,
                group=User.SYSUSER_GROUP
            )
            u.save()

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
