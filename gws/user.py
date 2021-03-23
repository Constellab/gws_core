# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from secrets import token_bytes
from base64 import b64encode
    
from peewee import  CharField, BooleanField, ForeignKeyField
from gws.model import Model
from gws.settings import Settings
from gws.logger import Error

# ####################################################################
#
# User class
#
# ####################################################################

class User(Model):
    
    token = CharField(null=False)
    email = CharField(default=False, index=True)
    group = CharField(default="default", index=True)
    is_active = BooleanField(default=True, index=True)
    is_locked = BooleanField(default=False, index=True)
    is_authenticated = BooleanField(default=False, index=True)

    VALID_GROUPS = ["user", "admin", "owner"]
    
    _is_deletable = False
    _table_name = 'gws_user'
    _fts_fields = {'full_name': 2.0}

    # -- A --
    
    @classmethod
    def authenticate(cls, uri: str, token: str) -> 'User':
        """ 
        Verify the uri and token, save the authentication status and returns the corresponding user

        :param uri: The user uri
        :type uri: str
        :param token: The token to check
        :type token: str
        :return: The user if successfully verified, False otherwise
        :rtype: User, False
        """
        
        with DbManager.db.atomic() as transaction:
            try:
                user = User.get(User.uri==uri, User.token==token)
                user.is_authenticated = True
                user.save()
                Activity.add(user, Activity.LOGIN)
                return user
            except:
                transaction.rollback()
                return False
    
    @classmethod
    def create_owner(cls):
        settings = Settings.retrieve()

        Q = User.select().where(User.group == "owner")
        if not Q:
            uri = settings.data["owner"]["uri"]
            email = settings.data["owner"]["email"]
            full_name = settings.data["owner"]["full_name"]
            u = User(
                uri = uri if uri else None, 
                email = email,
                data = {"full_name": full_name},
                group = "owner"
            )
            u.save()
            
    # -- G --
    
    @classmethod
    def get_owner(cls):
         return User.get(User.group == "owner")
    
    @property
    def full_name(self):
        return self.data.get("full_name", "")

    def __generate_token(self):
        return b64encode(token_bytes(32)).decode()
    
    def generate_access_token(self):
        self.token = self.__generate_token()
        self.save()
    
    # -- S --

    def save(self, *arg, **kwargs):
        if not self.group in self.VALID_GROUPS:
            raise Error("User", "save", "Invalid user group.")
        
        if self.id is None:
            if self.token is None:
                self.token = self.__generate_token()
        
        if self.group == "owner" or self.group == "admin":
            if not self.is_active or self.is_locked:
                raise Error("User", "save", "Cannot lock or deactivate the owner and the admin")
                
        return super().save(*arg, **kwargs)
    
    # -- U --
    
    @classmethod
    def unauthenticate(self, uri: str) -> 'User':
        with DbManager.db.atomic() as transaction:
            try:
                user = User.get(User.uri==uri, User.token==token)
                self.is_authenticated = False
                self.token = self.s__generate_token()     #/!\SECURITRY: cancel current token to prevent token hacking
                self.save()
                Activity.add(self, Activity.LOGOUT)
            except:
                transaction.rollback()
                return False
    
# ####################################################################
#
# Activity class
#
# ####################################################################

class Activity(Model):
    user = ForeignKeyField(User)
    _is_deletable = False
    
    _fts_fields = {'activity_type': 2.0, "object_type": 2.0, "object_uri": 1.0}
    _table_name = "gws_user_activity"
    
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    START = "START"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    
    @classmethod
    def add(self, user: User, activity_type: str, object_type=None, object_uri=None):
        ac = Activity(
            user=user, 
            data = {
                "activity_type": activity_type,
                "object_type": object_type,
                "object_uri": object_uri
            }
        )
        ac.save()