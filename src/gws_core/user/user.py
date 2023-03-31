# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import final

from peewee import BooleanField, CharField
from typing_extensions import NotRequired, TypedDict

from ..core.classes.enum_field import EnumField
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from .user_group import UserGroup


class UserTheme(Enum):
    LIGHT_THEME = 'light-theme'
    DARK_THEME = 'dark-theme'


class UserLanguage(Enum):
    EN = 'en'
    FR = 'fr'


class UserDataDict(TypedDict):
    id: str
    email: str
    first_name: str
    last_name: str
    group: str
    is_active: bool
    theme: NotRequired[str]
    lang: NotRequired[str]


# ####################################################################
#
# User class
#
# ####################################################################


@final
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
    theme: UserTheme = EnumField(choices=UserTheme,
                                 default=UserTheme.LIGHT_THEME)

    lang: UserLanguage = EnumField(choices=UserLanguage,
                                   default=UserLanguage.EN)

    _table_name = 'gws_user'

    def archive(self, archive: bool) -> None:
        """
        Archive method. This method is deactivated. Always returns False.
        """

        return None

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

    @property
    def full_name(self):
        return " ".join([self.first_name, self.last_name]).strip()

    @property
    def is_admin(self):
        return self.group == UserGroup.ADMIN

    @property
    def is_owner(self):
        return self.group == UserGroup.OWNER

    @property
    def is_sysuser(self):
        return self.group == UserGroup.SYSUSER

    def has_access(self, group: UserGroup) -> bool:
        """return true if the user group is equal or higher than the group
        """
        return self.group <= group

    def save(self, *arg, **kwargs) -> 'User':
        if not UserGroup.has_value(self.group):
            raise BadRequestException("Invalid user group")
        if self.is_owner or self.is_admin or self.is_sysuser:
            if not self.is_active:
                raise BadRequestException(
                    "Cannot deactivate the {owner, admin, system} users")
        return super().save(*arg, **kwargs)

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    def to_user_data_dict(self) -> UserDataDict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "group": self.group.value,
            "is_active": self.is_active,
            "theme": self.theme.value,
            "lang": self.lang.value
        }

    def from_user_data_dict(self, data: UserDataDict) -> None:
        self.email = data['email']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.group = UserGroup(data['group'])
        self.is_active = data['is_active']
        self.theme = UserTheme(data.get('theme', UserTheme.LIGHT_THEME.value))
        self.lang = UserLanguage(data.get('lang', UserLanguage.EN.value))
