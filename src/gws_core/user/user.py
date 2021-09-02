# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from gws_core.core.decorator.json_ignore import JsonIgnore
from peewee import BooleanField, CharField

from ..core.classes.enum_field import EnumField
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.utils import Utils
from ..model.typing_register_decorator import TypingDecorator
from ..user.user_group import UserGroup

# ####################################################################
#
# User class
#
# ####################################################################


@final
@JsonIgnore(["is_http_authenticated", "is_console_authenticated", "console_token"])
@TypingDecorator(unique_name="User", object_type="GWS_CORE", hide=True)
class User(Model):
    """
    User class

    :property email: The user email
    :type email: `str`
    :property group: The user group (`sysuser`, `admin`, `owner` or `user`)
    :type group: `str`
    :property is_active: True if the is active, False otherwise
    :type is_active: `bool`
    :property console_token: The token used to authenticate the user trough the console
    :type console_token: `str`
    :property console_token: The token used to authenticate the user trough the console
    :type console_token: `str`
    :property is_http_authenticated: True if the user authenticated through the HTTP context, False otherwise
    :type is_http_authenticated: `bool`
    :property is_console_authenticated: True if the user authenticated through the Console context, False otherwise
    :type is_console_authenticated: `bool`
    """

    email: str = CharField(default=False, index=True)
    first_name: str = CharField(default=False, index=True)
    last_name: str = CharField(default=False, index=True)
    group: UserGroup = EnumField(choices=UserGroup,
                                 default=UserGroup.USER)
    is_active = BooleanField(default=True)
    console_token = CharField(default="")
    is_http_authenticated = BooleanField(default=False)
    is_console_authenticated = BooleanField(default=False)

    _is_removable = False
    _table_name = 'gws_user'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.console_token:
            self.console_token = Utils.generate_random_chars(128)

    # -- A --

    def archive(self, archive: bool) -> None:
        """
        Archive method. This method is deactivated. Always returns False.
        """

        return None

    # -- G --

    @classmethod
    def get_admin(cls):
        return User.get(User.group == UserGroup.ADMIN)

    @classmethod
    def get_owner(cls):
        return User.get(User.group == UserGroup.OWNER)

    @classmethod
    def get_sysuser(cls):
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

    @property
    def is_authenticated(self):
        # get fresh data from DB
        user: User = User.get_by_id(self.id)
        return user.is_http_authenticated or user.is_console_authenticated

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

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the user.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: `bool`
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: `bool`
        :return: The representation
        :rtype: `dict`, `str`
        """

        _json = super().to_json(deep=deep, **kwargs)

        return _json

    # -- U --
