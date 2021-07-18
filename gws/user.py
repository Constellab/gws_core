# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from peewee import  CharField, BooleanField

from .logger import Error, Warning
from .settings import Settings
from .db.model import Model
from .utils import generate_random_chars

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
            self.console_token = generate_random_chars(128)
            
    # -- A --
    
    def archive(self, tf:bool)->bool:
        """
        Archive method. This method is deactivated. Always returns False.
        """
        
        return False
        
    @classmethod
    def authenticate(cls, uri: str, console_token: str = "") -> bool:
        """
        Authenticate a user
        
        :param uri: The uri of the user to authenticate
        :type uri: `str`
        :param console_token: The console token. This token is only used if the for console contexts
        :type console_token: `str`
        :return: True if the user is successfully autheticated, False otherwise
        :rtype: `bool`
        """
        
        from .service.http_service import HTTPService
        
        try:
            user = User.get(User.uri == uri)
        except Exception as err:
            raise Error("User", "authenticate", f"User not found with uri {uri}") from err
        if not user.is_active:
            return False
        if HTTPService.is_http_context():
            return cls.__authenticate_http(user)            
        else:
            return cls.__authenticate_console(user, console_token)
        
    @classmethod
    def __authenticate_console(cls, user, console_token) -> bool:
        from .service.user_service import UserService
        from .activity import Activity

        if user.is_console_authenticated:       
            UserService.set_current_user(user)
            return True
        is_valid_token = bool(console_token) and (user.console_token == console_token)
        if not is_valid_token:
            return False
        with cls._db_manager.db.atomic() as transaction:
            try:
                # authenticate the user first
                user.is_console_authenticated = True
                if user.save():
                    UserService.set_current_user(user)
                else:
                    raise Error("User", "__console_authenticate", "Cannot save user status")
                # now save user activity
                Activity.add(Activity.CONSOLE_AUTHENTICATION)
                return True
            except Exception as err:
                Warning("User", "__authenticate_console", f"{err}")
                transaction.rollback()
                return False
    
    @classmethod
    def __authenticate_http(cls, user) -> bool:
        from .service.user_service import UserService
        from .activity import Activity

        if user.is_http_authenticated:
            UserService.set_current_user(user)
            return True
        with cls._db_manager.db.atomic() as transaction:
            try:
                # authenticate the user first
                user.is_http_authenticated = True
                if user.save():
                    UserService.set_current_user(user)
                else:
                    raise Error("User", "__http_authenticate", "Cannot save user status")    
                # now save user activity
                Activity.add(Activity.HTTP_AUTHENTICATION)
                return True
            except Exception as err:
                Warning("User", "__authenticate_http", f"{err}")
                transaction.rollback()
                return False

    @classmethod
    def create_owner_and_sysuser(cls):
        settings = Settings.retrieve()
        Q = User.select().where(User.group == cls.OWNER_GROUP)
        if not Q:
            uri = settings.data["owner"]["uri"]
            email = settings.data["owner"]["email"]
            first_name = settings.data["owner"]["first_name"]
            last_name = settings.data["owner"]["last_name"]
            u = User(
                uri = uri if uri else None, 
                email = email,
                data = {"first_name": first_name, "last_name": last_name},
                is_active = True,
                group = cls.OWNER_GROUP
            )
            u.save()
        Q = User.select().where(User.group == cls.SYSUSER_GROUP)
        if not Q:
            u = User(
                email = "admin@gencovery.com",
                data = {"first_name": "sysuser", "last_name": ""},
                is_active = True,
                group = cls.SYSUSER_GROUP
            )
            u.save()
            
    # -- G --
    
    @classmethod
    def get_admin(cls):
        try:
            return User.get(User.group == cls.ADMIN_GROUP)
        except:
            cls.create_admin_user()
            return User.get(User.group == cls.ADMIN_GROUP)

    @classmethod
    def get_owner(cls):
        try:
            return User.get(User.group == cls.OWNER_GROUP)
        except:
            cls.create_owner_and_sysuser()
            return User.get(User.group == cls.OWNER_GROUP)
        
    @classmethod
    def get_sysuser(cls):
        try:
            return User.get(User.group == cls.SYSUSER_GROUP)
        except:
            cls.create_owner_and_sysuser()
            return User.get(User.group == cls.SYSUSER_GROUP)

    @classmethod
    def get_by_email(cls, email: str) -> 'User':
        try:
            return cls.get(cls.email == email)
        except:
            return None
    
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
            raise Error("User", "save", "Invalid user group")
        if self.is_owner or self.is_admin or self.is_sysuser:
            if not self.is_active:
                raise Error("User", "save", "Cannot deactivate the {owner, admin, system} users")    
        return super().save(*arg, **kwargs)
    
    # -- T --
        
    def to_json(self, *args, stringify: bool=False, prettify: bool=False, **kwargs) -> (dict, str, ):
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
    
    @classmethod
    def unauthenticate(cls, uri: str) -> bool:
        """
        Unauthenticate a user
        
        :param uri: The uri of the user to unauthenticate
        :type uri: `str`
        :return: True if the user is successfully unautheticated, False otherwise
        :rtype: `bool`
        """
        
        from .service.http_service import HTTPService
        
        try:
            user = User.get(User.uri == uri)
        except Exception as err:
            raise Error("User", "unauthenticate", f"User not found with uri {uri}") from err
        if not user.is_active:
            return False
        if HTTPService.is_http_context():
            return cls.__unauthenticate_http(user)            
        else:
            return cls.__unauthenticate_console(user)
    
    @classmethod
    def __unauthenticate_http(cls, user) -> bool:
        from .service.user_service import UserService
        from .activity import Activity

        if not user.is_http_authenticated:
            UserService.set_current_user(None)
            return True
        with cls._db_manager.db.atomic() as transaction:
            try:
                user.is_http_authenticated = False
                Activity.add(Activity.HTTP_UNAUTHENTICATION)
                if user.save():
                    UserService.set_current_user(None)
                else:
                    raise Error("User", "__unauthenticate_http", "Cannot save user status")
                return True
            except Exception as err:
                Warning("User", "__unauthenticate_http", f"{err}")
                transaction.rollback()
                return False
            
    @classmethod
    def __unauthenticate_console(cls, user) -> bool:
        from .service.user_service import UserService
        from .activity import Activity

        if not user.is_console_authenticated:
            UserService.set_current_user(None)
            return True
        with cls._db_manager.db.atomic() as transaction:
            try:
                user.is_console_authenticated = False
                Activity.add(Activity.CONSOLE_UNAUTHENTICATION)
                if user.save():
                    UserService.set_current_user(None)
                else:
                    raise Error("User", "__unauthenticate_console", "Cannot save user status")
                return True
            except Exception as err:
                Warning("User", "__unauthenticate_console", f"{err}")
                transaction.rollback()
                return False

    # -- V --
  