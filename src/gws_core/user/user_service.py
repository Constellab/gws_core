# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from .activity import Activity
from .user import User, UserDataDict
from .user_group import UserGroup


class UserService(BaseService):

    _console_data = {"user": None}

    # -- A --

    @classmethod
    def activate_user(cls, id) -> User:
        return cls.set_user_status(id, {"is_active": True})

    # -- C --

    @classmethod
    def create_user(cls, user: UserDataDict) -> User:

        if cls.user_exists(user["id"]):
            raise BadRequestException("The user already exists")

        return cls._create_user(user)

    @classmethod
    def create_user_if_not_exists(cls, user: UserDataDict) -> User:
        db_user: User = cls.get_user_by_id(user["id"])
        if db_user is not None:
            return db_user

        return cls._create_user(user)

    @classmethod
    def _create_user(cls, data: UserDataDict) -> User:
        group: UserGroup = UserGroup.from_string(data.get('group', None), UserGroup.USER)
        if group == UserGroup.SYSUSER:
            raise BadRequestException("Cannot create sysuser")

        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            group=group,
            is_active=data.get('is_active', True),
            data={
            }
        )
        # set the id later to mark the user as not saved
        user.id = data['id']
        user.save()
        return User.get_by_id(user.id)

    # -- D --

    @classmethod
    def deactivate_user(cls, id) -> User:
        return cls.set_user_status(id, {"is_active": False})

    # -- F --

    @classmethod
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
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def fetch_user(cls, id: str) -> User:
        return User.get_by_id(id)

    @classmethod
    def fetch_user_list(cls,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[User]:

        query = User.select().order_by(User.created_at.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    # -- G --

    @classmethod
    def get_user_by_id(cls, id: str) -> User:
        return User.get_by_id(id)

    @classmethod
    def get_user_by_email(cls, email: str) -> User:
        return User.get_by_email(email)

    # -- S --

    @classmethod
    def set_user_status(cls, id, data) -> User:
        user = User.get_by_id(id)
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
    def user_exists(cls, id: str) -> bool:
        return cls.get_user_by_id(id) is not None
