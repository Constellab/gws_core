# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Union

from peewee import BooleanField, CharField

from ..core.exception import BadRequestException
from ..core.model.model import Model
from ..core.utils.util import Util

# ####################################################################
#
# User class
#
# ####################################################################


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

    email = CharField(default=False, index=True)
    group = CharField(default="user", index=True)
    is_active = BooleanField(default=True)
    console_token = CharField(default="")
    is_http_authenticated = BooleanField(default=False)
    is_console_authenticated = BooleanField(default=False)

    SYSUSER_GROUP = "sysuser"  # privilege 0 (highest)
    ADMIN_GROUP = "admin"      # privilege 1
    OWNER_GROUP = "owner"      # privilege 2
    USER_GOUP = "user"         # privilege 3

    VALID_GROUPS = [USER_GOUP, ADMIN_GROUP, OWNER_GROUP, SYSUSER_GROUP]

    _is_removable = False
    _table_name = 'gws_user'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.console_token:
            self.console_token = Util.generate_random_chars(128)

    # -- A --

    def archive(self, archive: bool) -> bool:
        """
        Archive method. This method is deactivated. Always returns False.
        """

        return False

    # -- G --

    @classmethod
    def get_admin(cls):
        return User.get(User.group == cls.ADMIN_GROUP)

    @classmethod
    def get_owner(cls):
        return User.get(User.group == cls.OWNER_GROUP)

    @classmethod
    def get_sysuser(cls):
        return User.get(User.group == cls.SYSUSER_GROUP)

    @classmethod
    def get_by_email(cls, email: str) -> 'User':
        return User.get(User.email == email)

    # -- F --

    @property
    def first_name(self):
        return self.data.get("first_name", "")

    @property
    def full_name(self):
        first_name = self.data.get("first_name", "")
        last_name = self.data.get("last_name", "")
        return " ".join([first_name, last_name]).strip()

    # -- I --

    @property
    def is_admin(self):
        return self.group == self.ADMIN_GROUP

    @property
    def is_owner(self):
        return self.group == self.OWNER_GROUP

    @property
    def is_sysuser(self):
        return self.group == self.SYSUSER_GROUP

    @property
    def is_authenticated(self):
        # get fresh data from DB
        user = User.get_by_id(self.id)
        return user.is_http_authenticated or user.is_console_authenticated

    # -- L --

    @property
    def last_name(self):
        return self.data.get("last_name", "")

    # -- S --

    def save(self, *arg, **kwargs):
        if not self.group in self.VALID_GROUPS:
            raise BadRequestException("Invalid user group")
        if self.is_owner or self.is_admin or self.is_sysuser:
            if not self.is_active:
                raise BadRequestException(
                    "Cannot deactivate the {owner, admin, system} users")
        return super().save(*arg, **kwargs)

    # -- T --

    def to_json(self, *args, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[dict, str]:
        """
        Returns a JSON string or dictionnary representation of the user.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: `bool`
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: `bool`
        :return: The representation
        :rtype: `dict`, `str`
        """

        _json = super().to_json(*args, **kwargs)
        del _json["console_token"]
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- U --
