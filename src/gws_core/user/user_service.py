# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core.core.utils.logger import Logger
from gws_core.space.space_service import SpaceService
from gws_core.user.user_dto import UserData

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from .activity import Activity
from .user import User, UserDataDict
from .user_group import UserGroup


class UserService(BaseService):

    _console_data = {"user": None}

    @classmethod
    def activate_user(cls, id: str) -> User:
        return cls.set_user_active(id, True)

    @classmethod
    def create_space_user(cls, user: UserData) -> User:
        db_user: User = cls.get_user_by_id(user.id)

        if db_user is None:
            return cls._create_user(user.dict())
        else:
            db_user.email = user.email
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.group = user.group
            db_user.is_active = user.is_active
            return db_user.save()

    @classmethod
    def create_user_if_not_exists(cls, user: UserDataDict) -> User:
        db_user: User = cls.get_user_by_id(user["id"])
        if db_user is not None:
            db_user.from_user_data_dict(user)
            return db_user.save()

        return cls._create_user(user)

    @classmethod
    def _create_user(cls, data: UserDataDict) -> User:
        group: UserGroup = UserGroup(data['group'])
        if group == UserGroup.SYSUSER:
            raise BadRequestException("Cannot create sysuser")

        user = User(data={})
        # set the id later to mark the user as not saved
        user.id = data["id"]
        user.from_user_data_dict(data)
        user.save()
        return User.get_by_id(user.id)

    @ classmethod
    def deactivate_user(cls, id) -> User:
        return cls.set_user_active(id, False)

    @ classmethod
    def fecth_activity_list(cls,
                            user_id: str = None,
                            activity_type: str = None,
                            page: int = 0,
                            number_of_items_per_page: int = 20) -> Paginator[User]:

        query = Activity.select().order_by(Activity.created_at.desc())
        if user_id:
            query = query.join(User).where(User.id == user_id)
        if activity_type:
            query = query.where(Activity.activity_type ==
                                activity_type.upper())
        return Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_by_id_or_none(cls, id: str) -> User:
        return User.get_by_id(id)

    @classmethod
    def fetch_user_list(cls,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[User]:

        query = User.select().order_by(User.created_at.desc())
        return Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_user_by_id(cls, id: str) -> User:
        return User.get_by_id(id)

    @classmethod
    def get_user_by_email(cls, email: str) -> User:
        return User.get_by_email(email)

    @classmethod
    def set_user_active(cls, id: str, is_active: bool) -> User:
        user: User = User.get_by_id_and_check(id)

        user.is_active = is_active
        return user.save()

    @classmethod
    def get_all_users(cls) -> List[User]:
        return list(User.select())

    @classmethod
    def get_all_real_users(cls) -> List[User]:
        return list(User.select().where(User.group != UserGroup.SYSUSER)
                    .order_by(User.last_name, User.first_name))

    # Create the admin
    @classmethod
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
    def user_exists(cls, id: str) -> bool:
        return cls.get_user_by_id(id) is not None

    @classmethod
    def synchronize_all_space_users(cls) -> None:
        Logger.info("Synchronizing users from space")
        try:
            users = SpaceService.get_all_lab_users()
            for user in users:
                cls.create_space_user(user)

            Logger.info(f"{len(users)} synchronized users from space")
        except Exception as err:
            Logger.error(f"Error while synchronizing users: {err}")
            raise err
