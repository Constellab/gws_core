# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from gws_core.user.user_dto import UserDataDict
from peewee import BooleanField, CharField

from ..core.classes.enum_field import EnumField
from ..core.decorator.json_ignore import json_ignore
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.utils import Utils
from ..model.typing_register_decorator import typing_registrator
from .user_group import UserGroup

# ####################################################################
#
# User class
#
# ####################################################################


@final
@typing_registrator(unique_name="User", object_type="MODEL", hide=True)
class User(Model):
    """
    User class

    :property email: The user email
    :type email: `str`
    :property group: The user group (`sysuser`, `admin`, `owner` or `user`)
    :type group: `str`
    :property is_active: True if the is active, False otherwise
    :type is_active: `bool`
    """

    email: str = CharField(default=False, index=True)
    first_name: str = CharField(default=False)
    last_name: str = CharField(default=False)
    group: UserGroup = EnumField(choices=UserGroup,
                                 default=UserGroup.USER)
    is_active = BooleanField(default=True)

    _table_name = 'gws_user'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # -- A --

    def archive(self, archive: bool) -> None:
        """
        Archive method. This method is deactivated. Always returns False.
        """

        return None

    # -- G --

    @classmethod
    def get_admin(cls) -> 'User':
        return User.get(User.group == UserGroup.ADMIN)

    @classmethod
    def get_owner(cls) -> 'User':
        return User.get(User.group == UserGroup.OWNER)

    @classmethod
    def get_sysuser(cls) -> 'User':
        return User.get(User.group == UserGroup.SYSUSER)

    @classmethod
    def get_by_email(cls, email: str) -> 'User':
        return User.get(User.email == email)

    # -- F --

    @property
    def full_name(self):
        return " ".join([self.first_name, self.last_name]).strip()

    # -- I --

    @property
    def is_admin(self):
        return self.group == UserGroup.ADMIN

    @property
    def is_owner(self):
        return self.group == UserGroup.OWNER

    @property
    def is_sysuser(self):
        return self.group == UserGroup.SYSUSER

    # -- L --

    def has_access(self, group: UserGroup) -> bool:
        """return true if the user group is equal or higher than the group
        """
        return self.group <= group

    # -- S --

    def save(self, *arg, **kwargs) -> 'User':
        if not UserGroup.has_value(self.group):
            raise BadRequestException("Invalid user group")
        if self.is_owner or self.is_admin or self.is_sysuser:
            if not self.is_active:
                raise BadRequestException(
                    "Cannot deactivate the {owner, admin, system} users")
        return super().save(*arg, **kwargs)

    # -- T --

    # -- U --

    def to_user_data_dict(self) -> UserDataDict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "group": self.group.value,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
        }
