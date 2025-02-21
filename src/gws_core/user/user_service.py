

from typing import List, Union

from gws_core.core.utils.logger import Logger
from gws_core.space.space_service import SpaceService
from gws_core.user.user_dto import UserFullDTO

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import BadRequestException
from .user import User
from .user_group import UserGroup


class UserService():

    @classmethod
    def activate_user(cls, id_: str) -> User:
        return cls.set_user_active(id_, True)

    @classmethod
    def create_or_update_user_dto(cls, user_dto: UserFullDTO) -> User:
        db_user: User | None = cls.get_user_by_id(user_dto.id)
        if db_user is not None:
            db_user.from_full_dto(user_dto)
            return db_user.save()

        return cls._create_user(user_dto)

    @classmethod
    def _create_user(cls, user_dto: UserFullDTO) -> User:
        if user_dto.group == UserGroup.SYSUSER:
            raise BadRequestException("Cannot create sysuser")

        user = User(data={})
        # set the id_ later to mark the user as not saved
        user.id = user_dto.id
        user.from_full_dto(user_dto)
        user.save()
        return User.get_by_id(user.id)

    @classmethod
    def deactivate_user(cls, id_: str) -> User:
        return cls.set_user_active(id_, False)

    @classmethod
    def get_by_id_or_none(cls, id_: str) -> Union[User, None]:
        return User.get_by_id(id_)

    @classmethod
    def get_by_id_and_check(cls, id_: str) -> User:
        return User.get_by_id_and_check(id_)

    @classmethod
    def get_user_by_id(cls, id_: str) -> User | None:
        return User.get_by_id(id_)

    @classmethod
    def get_user_by_email(cls, email: str) -> User | None:
        return User.get_by_email(email)

    @classmethod
    def set_user_active(cls, id_: str, is_active: bool) -> User:
        user: User = User.get_by_id_and_check(id_)

        if not is_active:
            if user.is_sysuser:
                raise BadRequestException("Cannot deactivate the system user")
            if user.is_admin:
                # check if this is the last admin
                if User.select().where((User.group == UserGroup.ADMIN) & (User.is_active == True)).count() == 1:
                    raise BadRequestException("Cannot deactivate the last admin")

        user.is_active = is_active
        return user.save()

    @classmethod
    def get_all_users(cls) -> List[User]:
        return list(User.select())

    @classmethod
    def get_all_real_users(cls) -> List[User]:
        return list(User.select().where(User.group != UserGroup.SYSUSER)
                    .order_by(User.first_name, User.last_name))

    # Create the admin
    @classmethod
    def create_sysuser(cls):
        """ Create the system user """
        try:
            UserService.get_sysuser()
        except:
            user = User(
                email="admin@gencovery.com",
                first_name="System",
                last_name="User",
                data={},
                is_active=True,
                group=UserGroup.SYSUSER
            )
            user.save()

    @classmethod
    def get_sysuser(cls):
        return User.get_sysuser()

    @classmethod
    def user_exists(cls, id_: str) -> bool:
        return cls.get_user_by_id(id_) is not None

    @classmethod
    def synchronize_all_space_users(cls) -> None:
        Logger.info("Synchronizing users from space")
        try:
            users = SpaceService.get_instance().get_all_lab_users()
            for user in users:
                cls.create_or_update_user_dto(user)

            Logger.info(f"{len(users)} synchronized users from space")
        except Exception as err:
            Logger.error(f"Error while synchronizing users: {err}")
            raise err

    @classmethod
    def smart_search_by_name(cls, name: str, page: int = 0,
                             number_of_items_per_page: int = 20) -> Paginator[User]:
        name_parts = name.split(" ")
        # if name does not contain space, search by first name or last name
        if len(name_parts) == 1:
            model_select = User.search_by_firstname_or_lastname(name)

            return Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

        # if there are 2 words, search by lastname and firstname
        elif len(name_parts) == 2:
            model_select = User.search_by_firstname_and_lastname(name_parts[0], name_parts[1])

            paginator = Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

            # if nothing is found, search by lastname or firstname
            if paginator.page_info.total_number_of_items > 0:
                return paginator

        model_select = User.search_by_firstname_or_lastname(name)
        return Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_or_import_user_info(cls, user_id: str) -> User:
        """ Get the user info from the database.
         If he doesn"t exist, get it from the space (this might import a user that is not active in the lab)

        :param user_id: _description_
        :type user_id: str
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: User
        """
        user = cls.get_user_by_id(user_id)
        if user is not None:
            return user

        user = SpaceService.get_instance().get_user_info(user_id)
        if user is None:
            raise BadRequestException("The user does not exist in Constellab")
        return cls.create_or_update_user_dto(user)
