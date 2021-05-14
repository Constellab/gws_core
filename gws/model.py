# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

import sys
import os
import asyncio
import concurrent.futures
import uuid
import inspect
import hashlib
import urllib.parse
import json
import jwt
import zlib
import importlib
import shutil
import re
import collections
import time
from subprocess import DEVNULL
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from peewee import SqliteDatabase, Model as PWModel
from peewee import  Field, IntegerField, FloatField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField, ManyToManyField, IPField, TextField, BlobField, \
                    AutoField, BigAutoField
from playhouse.sqlite_ext import JSONField, SearchField, RowIDField

from gws.logger import Error, Info, Warning
from gws.settings import Settings
from gws.event import EventListener
from gws.io import Input, Output, InPort, OutPort, Connector, Interface, Outerface
from gws.utils import to_camel_case, sort_dict_by_key, generate_random_chars
from gws.http import *

from gws.base import format_table_name, slugify, BaseModel, BaseFTSModel, DbManager

# ####################################################################
#
# Model class
#
# ####################################################################
 
class Model(BaseModel):
    """
    Model class

    :property id: The id of the model (in database)
    :type id: `int`
    :property uri: The unique resource identifier of the model
    :type uri: `str`
    :property type: The type of the model (the full class name)
    :type type: `str`
    :property creation_datetime: The creation datetime of the model
    :type creation_datetime: `datetime`
    :property save_datetime: The last save datetime in database
    :type save_datetime: `datetime`
    :property is_archived: True if the model is archived, False otherwise. Defaults to False
    :type is_archived: `bool`
    :property data: The data of the model
    :type data: `dict`
    :property hash: The hash of the model
    :type hash: `str`
    """
    
    id = IntegerField(primary_key=True)
    uri = CharField(null=True, index=True)
    type = CharField(null=True, index=True)
    creation_datetime = DateTimeField(default=datetime.now, index=True)
    save_datetime = DateTimeField(index=True)
    is_archived = BooleanField(default=False, index=True)
    hash = CharField(null=True, index=True)
    data = JSONField(null=True)
    
    _kv_store: 'KVStore' = None
    _is_singleton = False
    _is_removable = True
    
    _fts_fields = {}
    _is_fts_active = True
    
    _table_name = 'gws_model'
    
    settings = Settings.retrieve()
    _LAB_URI = settings.get_data("uri")
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.id and self._is_singleton:
            try:
                cls = type(self)
                model = cls.get(cls.type == self.full_classname())
            except:
                model = None
            
            if model:
                # /!\ Shallow copy all properties (i.e. object cast) 
                # Prevent creating duplicates of processes having a representation in the db.
                for prop in model.property_names(Field):
                    val = getattr(model, prop)
                    setattr(self, prop, val) 
        
        if self.uri is None:
            self.uri = str(uuid.uuid4())

        if self.data is None:
            self.data = {}

        # ensures that field type is allways equal to the name of the class
        if self.type is None:
            self.type = self.full_classname()
        elif self.type != self.full_classname():
            # allow object cast after ...
            pass
        
        from gws.store import KVStore
        self._kv_store = KVStore(self.kv_store_path)

    # -- A --
    
    def archive(self, tf: bool) -> bool:
        """
        Archive of Unarchive the model
        
        :param tf: True to archive, False to unarchive
        :type tf: `bool`
        :return: True if sucessfully done, False otherwise
        :rtype: `bool`
        """
        
        if self.is_archived == tf:
            return True
        
        self.is_archived = tf
        cls = type(self)
        return self.save(only=[cls.is_archived])
        
    # -- B --
    
    @staticmethod
    def barefy( data: dict, sort_keys=False ):
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=sort_keys)
        data = re.sub(r"\"(([^\"]*_)?uri|save_datetime|creation_datetime|hash)\"\s*\:\s*\"([^\"]*)\"", r'"\1": ""', data)
        return json.loads(data)
    
    # -- C --
    
    def __create_hash_object(self):
        h = hashlib.blake2b()
        h.update(self._LAB_URI.encode())
        exclusion_list = (ForeignKeyField, JSONField, ManyToManyField, BlobField, AutoField, BigAutoField, )
        for prop in self.property_names(Field, exclude=exclusion_list) :
            if prop in ["id", "hash"]:
                continue
            val = getattr(self, prop)            
            h.update( str(val).encode() )
         
        for prop in self.property_names(JSONField):
            val = getattr(self, prop)
            h.update( json.dumps(val, sort_keys=True).encode() )
            
        for prop in self.property_names(BlobField):
            val = getattr(self, prop)
            h.update( val )
            
        for prop in self.property_names(ForeignKeyField):
            val = getattr(self, prop)
            if isinstance(val, Model):
                h.update( val.hash.encode() )

        return h
    
    def __compute_hash(self):
        ho = self.__create_hash_object()
        return ho.hexdigest()

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database

        :return: The model
        :rtype: `Model` instance
        """
        
        from .service.model_service import ModelService
        
        if self.type == self.full_classname():
            return self
        
        # instanciate the class and shallow copy data
        new_model_t = ModelService.get_model_type(self.type)
        model = new_model_t()
        for prop in self.property_names(Field):
            val = getattr(self, prop)
            setattr(model, prop, val)

        return model

    def clear_data(self, save: bool = False):
        """
        Clears the `data`
    
        :param save: If True, save the model the `data` is cleared
        :type save: bool
        """
        self.data = {}
        if save:
            self.save()

    @classmethod
    def create_table(cls, *args, **kwargs):
        if cls.table_exists():
            return

        if cls.fts_model():
            cls.fts_model().create_table()

        super().create_table(*args, **kwargs)

    # -- D --

    def delete_instance(self, *args, **kwargs):
        self.kv_store.remove()
        super().delete_instance(*args, **kwargs)
        
    @classmethod
    def drop_table(cls):
        if cls.fts_model():
            cls.fts_model().drop_table()
        
        from gws.store import KVStore
        KVStore.remove_all(folder=cls._table_name)
        
        super().drop_table()

    # -- E --
        
    def __eq__(self, other: 'Model') -> bool:
        """ 
        Compares the model with another model. The models are equal if they are 
        identical (same handle in memory) or have the same id in the database

        :param other: The model to compare
        :type other: `Model`
        :return: True if the models are equal
        :rtype: bool
        """
        if not isinstance(other, Model):
            return False

        return (self is other) or ((self.id != None) and (self.id == other.id))
    
    # -- F --

    def fetch_type_by_id(self, id) -> 'type':
        """ 
        Fecth the model type (string) by its `id` from the database and return the corresponding python type.
        Use the proper table even if the table name has changed.

        :param id: The id of the model
        :type id: int
        :return: The model type
        :rtype: type
        """
        
        from .service.model_service import ModelService
        
        cursor = DbManager.db.execute_sql(f'SELECT type FROM {self._table_name} WHERE id = ?', (str(id),))
        row = cursor.fetchone()
        if len(row) == 0:
            raise Error("gws.model.Model", "fetch_type_by_id", "The model is not found.")
        type_str = row[0]
        model_t = ModelService.get_model_type(type_str)
        return model_t

    # -- G --

    @staticmethod
    def get_brick_dir(brick_name: str):
        settings = Settings.retrieve()
        return settings.get_dependency_dir(brick_name)
        
    @classmethod
    def fts_model(cls):
        if not cls._fts_fields:
            return None
        
        fts_class_name = to_camel_case(cls._table_name, capitalize_first=True) + "FTSModel"
        
        _FTSModel = type(fts_class_name, (BaseFTSModel, ), {
            "_related_model" : cls
        })

        return _FTSModel

    @classmethod
    def get_by_uri(cls, uri: str) -> str:
        try:
            return cls.get(cls.uri == uri)
        except:
            return None

    # -- H --

    def hydrate_with(self, data):
        """
        Hydrate the model with data
        """

        col_names = self.property_names(Field)
        for prop in data:
            if prop == "id":
                continue

            if prop in col_names:
                setattr(self, prop, data[prop])
            else:
                self.data[prop] = data[prop]

    # -- I --

    def is_saved(self):
        """ 
        Returns True if the model is saved in db, False otherwise

        :return: True if the model is saved in db, False otherwise
        :rtype: bool
        """
        return bool(self.id)

    # -- N -- 

    # -- K --

    @property
    def kv_store(self) -> 'KVStore':
        """ 
        Returns the path of the KVStore of the model

        :return: The path of the KVStore
        :rtype: str
        """
        return self._kv_store
    
    @property
    def kv_store_path(self) -> str:
        """ 
        Returns the path of the KVStore of the model

        :return: The path of the KVStore
        :rtype: str
        """
        return os.path.join(self._table_name, self.uri)
    
    # -- R --
    
    def refresh(self):
        """ 
        Refresh a model using db value

        :return: The path of the KVStore
        :rtype: str
        """
        
        cls = type(self)
        if self.id:
            db_object = cls.get_by_id(cls.id)
            for prop in db_object.property_names(Field):
                db_val = getattr(db_object, prop)
                setattr(self, prop, db_val) 

    # -- S --

    @classmethod
    def select(cls, *args, **kwargs):
        if not cls.table_exists():
            cls.create_table()
            
        return super().select(*args, **kwargs)

    @classmethod
    def select_me(cls, *args, **kwargs):
        if not cls.table_exists():
            cls.create_table()

        return cls.select( *args, **kwargs ).where(cls.type == cls.full_classname())
    
    @classmethod
    def search(cls, phrase, page:int = 1, number_of_items_per_page: int=20):
        _FTSModel = cls.fts_model()

        if _FTSModel is None:
            raise Error("gws.model.Model", "search", "No FTSModel model defined")
        
        return _FTSModel.search_bm25(
            phrase, 
            weights={'title': 2.0, 'content': 1.0},
            with_score=True,
            score_alias='search_score'
        )

    def set_data(self, data: dict):
        """ 
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input parameter data is not a `dict`
        """
        if isinstance(data,dict):
            self.data = data
        else:
            raise Error("gws.model.Model", "set_data","The data must be a JSONable dictionary")

    def _save_fts_document(self):
        _FTSModel = self.fts_model()

        if _FTSModel is None:
            return True  #-> no fts fields given -> nothing to do!
        
        try:
            doc = _FTSModel.get_by_id(self.id)  
        except:
            doc = _FTSModel(rowid=self.id)

        title = []
        content = []

        for field in self._fts_fields:
            score = self._fts_fields[field]
            if field in self.data:
                if score > 1:
                    if isinstance(self.data[field], list):
                        title.append( "\n".join([str(k) for k in self.data[field]]) )
                    else:
                        title.append(str(self.data[field]))
                else:
                    content.append(str(self.data[field]))

        doc.title = '\n'.join(title)
        doc.content = '\n'.join(content)

        return doc.save()


    def save(self, *args, **kwargs) -> bool:
        """ 
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input data is not a `dict`
        """

        if not self.table_exists():
            self.create_table()

        _FTSModel = self.fts_model()

        with DbManager.db.atomic() as transaction:
            try:
                if self._is_fts_active:
                    if not self._save_fts_document():
                        raise Error("gws.model.Model", "save", "Cannot save related FTS document")

                #self.kv_store.save()
                self.save_datetime = datetime.now()
                self.hash = self.__compute_hash()
                return super().save(*args, **kwargs)
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Model", "save", f"Error message: {err}")



    @classmethod
    def save_all(cls, model_list: list = None) -> bool:
        """
        Automically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.

        :param model_list: List of models
        :type model_list: list
        :return: True if all the model are successfully saved, False otherwise. 
        :rtype: bool
        """
        with DbManager.db.atomic() as transaction:
            try:
                #if model_list is None:
                #    return
                
                for m in model_list:
                    #if isinstance(m, cls):
                    m.save()
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Model", "save_all", f"Error message: {err}")

        return True
    
    # -- T --
    
    def to_json(self, *, show_hash=False, bare: bool=False, stringify: bool=False, prettify: bool=False, jsonifiable_data_keys: list=[], **kwargs) -> (str, dict, ):
        """
        Returns a JSON string or dictionnary representation of the model.

        :param show_hash: If True, returns the hash. Defaults to False
        :type show_hash: `bool`
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: `bool`
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: `bool`
        :param jsonifiable_data_keys: If is empty, `data` is fully jsonified, otherwise only specified keys are jsonified
        :type jsonifiable_data_keys: `list` of `str`        
        :return: The representation
        :rtype: `dict`, `str`
        """
      
        _json = {}
        
        jsonifiable_data_keys
        if not isinstance(jsonifiable_data_keys, list):
            jsonifiable_data_keys = []

        exclusion_list = (ForeignKeyField, ManyToManyField, BlobField, AutoField, BigAutoField, )

        for prop in self.property_names(Field, exclude=exclusion_list) :
            if prop in ["id"]:
                continue

            if prop.startswith("_"):
                continue  #-> private or protected property

            val = getattr(self, prop)

            if prop == "data":
                _json[prop] = {}

                if len(jsonifiable_data_keys) == 0:
                    _json[prop] = jsonable_encoder(val)
                else:
                    for k in jsonifiable_data_keys:
                        if k in val:
                            _json[prop][k] = jsonable_encoder(val[k])
            else:
                _json[prop] = jsonable_encoder(val)
                if bare:
                    if prop == "uri" or prop == "hash" or isinstance(val, (datetime, DateTimeField, DateField)):
                        _json[prop] = ""

        if not show_hash:
            del _json["hash"]

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- U --
    
    @property
    def user_data(self) -> dict:
        """
        Get user data
        
        :return: User data
        :rtype: `dict`
        """
        
        if not "_user_data_" in self.data:
            self.data["_user_data_"] = {}
            
        return self.data["_user_data_"]
    
    # -- V --
    
    def verify_hash(self) -> bool:
        """
        Verify the current hash of the model
        
        :return: True if the hash is valid, False otherwise
        :rtype: `bool`
        """
        
        return self.hash == self.__compute_hash()
    
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
    _fts_fields = {'first_name': 2.0, 'last_name': 2.0}
    
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
        except:
            raise Error("User", "authenticate", f"User not found with uri {uri}")

        if not user.is_active:
            return False
        
        if HTTPService.is_http_context():
            return cls.__authenticate_http(user)            
        else:
            return cls.__authenticate_console(user, console_token)
        
    @classmethod
    def __authenticate_console(cls, user, console_token) -> bool:
        from .service.user_service import UserService
        
        if user.is_console_authenticated:       
            UserService.set_current_user(user)
            return True
        
        is_valid_token = bool(console_token) and (user.console_token == console_token)
        if not is_valid_token:
            return False

        with DbManager.db.atomic() as transaction:
            try:
                # authenticate the user first
                user.is_console_authenticated = True
                if user.save():
                    UserService.set_current_user(user)
                else:
                    raise Error("User", "__console_authenticate", "Cannot save user status")
                
                # now save user activity
                Activity.add(
                    Activity.CONSOLE_AUTHENTICATION
                )
   
                return True
            except:
                transaction.rollback()
                return False
    
    @classmethod
    def __authenticate_http(cls, user) -> bool:
        from .service.user_service import UserService
        
        if user.is_http_authenticated:
            UserService.set_current_user(user)
            return True

        with DbManager.db.atomic() as transaction:
            try:
                # authenticate the user first
                user.is_http_authenticated = True
                if user.save():
                    UserService.set_current_user(user)
                else:
                    raise Error("User", "__http_authenticate", "Cannot save user status")
                    
                # now save user activity
                Activity.add(
                    Activity.HTTP_AUTHENTICATION
                )
                
                return True
            except Exception as err:
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
                email = "sysuser@local",
                data = {"first_name": "sysuser", "last_name": ""},
                is_active = True,
                group = cls.SYSUSER_GROUP
            )
            u.save()
            
    # -- G --
    
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
        except:
            raise Error("User", "unauthenticate", f"User not found with uri {uri}")
            
        if not user.is_active:
            return False
        
        if HTTPService.is_http_context():
            return cls.__unauthenticate_http(user)            
        else:
            return cls.__unauthenticate_console(user)
    
    @classmethod
    def __unauthenticate_http(cls, user) -> bool:
        from .service.user_service import UserService
        
        if not user.is_http_authenticated:
            UserService.set_current_user(None)
            return True
        
        with DbManager.db.atomic() as transaction:
            try:
                user.is_http_authenticated = False
                Activity.add(
                    Activity.HTTP_UNAUTHENTICATION
                )
                if user.save():
                    UserService.set_current_user(None)
                else:
                    raise Error("User", "__unauthenticate_http", "Cannot save user status")
                
                return True
            except:
                transaction.rollback()
                return False
            
    @classmethod
    def __unauthenticate_console(cls, user) -> bool:
        from .service.user_service import UserService
        
        if not user.is_console_authenticated:
            UserService.set_current_user(None)
            return True
        
        with DbManager.db.atomic() as transaction:
            try:
                user.is_console_authenticated = False
                Activity.add(
                    Activity.CONSOLE_UNAUTHENTICATION
                )
                if user.save():
                    UserService.set_current_user(None)
                else:
                    raise Error("User", "__unauthenticate_console", "Cannot save user status")
                
                return True
            except:
                transaction.rollback()
                return False
            
# ####################################################################
#
# Activity class
#
# ####################################################################

class Activity(Model):
    user = ForeignKeyField(User, null=False, index=True)
    activity_type = CharField(null=False, index=True)
    object_type = CharField(null=True, index=True)
    object_uri = CharField(null=True, index=True)
    
    _is_removable = False
    
    _fts_fields = {}
    _table_name = "gws_user_activity"
    
    CREATE = "CREATE"
    SAVE = "SAVE"
    START = "START"
    STOP = "STOP"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    VALIDATE = "VALIDATE"
    HTTP_AUTHENTICATION = "HTTP_AUTHENTICATION"
    HTTP_UNAUTHENTICATION = "HTTP_UNAUTHENTICATION"
    CONSOLE_AUTHENTICATION = "CONSOLE_AUTHENTICATION"
    CONSOLE_UNAUTHENTICATION = "CONSOLE_UNAUTHENTICATION"
    
    def archive(self, tf:bool)->bool:
        """
        Deactivated method. Allways returns False.
        """
        
        return False
    
    @classmethod
    def add(self, activity_type: str, *, object_type=None, object_uri=None, user=None):
        from .service.user_service import UserService
        
        if not user:
            user = UserService.get_current_user()
            
        activity = Activity(
            user = user, 
            activity_type = activity_type,
            object_type = object_type,
            object_uri = object_uri
        )
        activity.save()
    
    # -- T --
    
    def to_json(self, *, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json["user"] = {
            "uri": self.user.uri,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json   
        
# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):

    _fts_field = {'title': 2.0, 'description': 1.0}

    # -- A --

    def archive(self, tf: bool)->bool:
        """
        Archive of Unarchive Viewable and all its ViewModels
        
        :param tf: True to archive, False to unarchive
        :type tf: `bool`
        :return: True if sucessfully done, False otherwise
        :rtype: `bool`
        """
        
        if self.is_archived == tf:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                Q = ViewModel.select().where( 
                    (ViewModel.model_id == self.id) & 
                    (ViewModel.is_archived == (not tf))
                )
                
                for vm in Q:
                    if not vm.archive(tf):
                        transaction.rollback()
                        return False
                
                if super().archive(tf):
                    return True
                else:
                    transaction.rollback()
                    return False
            except Exception as err:
                Warning(err)
                transaction.rollback()
                return False

    # -- C --

    # -- D --
    
    @property
    def description(self) -> str:
        """
        Returns the description. Alias of :meth:`get_description`
        
        :return: The description
        :rtype: str
        """
        
        return self.data.get("description","")
    
    @description.setter
    def description(self, text:str):
        """
        Set the description. Alias of :meth:`set_description`
        
        :param text: The description test
        :type text: str
        """
        
        self.set_description(text)

    # -- G --
    
    def get_description(self, default="") -> str:
        """
        Returns the description
        
        :return: The description
        :rtype: str
        """
        
        return self.data.get("description", default)

    def get_title(self, default="") -> str:
        """ 
        Get the title
        """
        
        return self.data.get("title", default) #.capitalize()

    # -- R -- 

    # -- S --

    def set_title(self, title: str):
        """ 
        Set the title

        :param title: The title
        :type title: str
        """
        
        if self.data is None:
            self.data = {}
            
        self.data["title"] = title
        
    def set_description(self, text: str):
        """ 
        Set the description

        :param text: The description text
        :type text: str
        """
        
        if self.data is None:
            self.data = {}
            
        self.data["description"] = text
    
    # -- T --
    
    @property
    def title(self):
        """ 
        Get the title. Alias of :meth:`get_title`
        """
        
        return self.data.get("title", "")
    
    @title.setter
    def title(self, text:str):
        """ 
        Set the title. Alias of :meth:`set_title`
        """
        
        self.set_title(text)
    
    # -- V --

    def view(self, *args, params:dict = {}) -> 'ViewModel':
        """ 
        Build and return a ViewModel
        """
        
        if not isinstance(params, dict):
            params = {}

        view_model = ViewModel.get_instance(self, params)
        return view_model
                
    @property
    def view_models(self):
        """ 
        Get all the ViewModels of the Viewable
        """
        
        return ViewModel.select().where(ViewModel.model_id == self.id)
    
# ####################################################################
#
# Config class
#
# ####################################################################

class Config(Viewable):
    """
    Config class that represents the configuration of a process. A configuration is
    a collection of parameters
    """
    
    _table_name = 'gws_config'

    def __init__(self, *args, specs: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self.data = {
                "specs": {},
                "params": {}
            }
            
        if not specs is None:
            if not isinstance(specs, dict):
                raise Error("gws.model.Config", "__init__", f"The specs must be a dictionnary")
            
            #convert type to str
            from gws.validator import Validator
            for k in specs:
                if isinstance(specs[k]["type"], type):
                    specs[k]["type"] = specs[k]["type"].__name__ 

                default = specs[k].get("default", None)
                if not default is None:
                    #param_t = specs[k]["type"]
                    try:
                        validator = Validator.from_specs(**specs[k])
                        default = validator.validate(default)
                        specs[k]["default"] = default
                    except Exception as err:
                        raise Error("gws.model.Config", "__init__", f"Invalid default config value. Error message: {err}")

            self.set_specs( specs )

    # -- A --

    def archive(self, tf: bool)->bool:
        """ 
        Archive the config

        :param tf: True to archive, False to unarchive
        :type: `bool`
        :return: True if successfully archived, False otherwise
        :rtype: `bool`
        """
        
        some_processes_are_in_invalid_archive_state = Process.select().where( 
            (Process.config == self) & (Process.is_archived == (not tf) ) 
        ).count()
        
        if some_processes_are_in_invalid_archive_state:
            return False
 
        return super().archive(tf)
    
    # -- C --
    
    # -- D --

    # -- G --

    def get_param(self, name: str) -> (str, int, float, bool,):
        """ 
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """
        if not name in self.specs:
            raise Error("gws.model.Config", "get_param", f"Parameter {name} does not exist'")
        
        default = self.specs[name].get("default", None)
        return self.data["params"].get(name,default)

    # -- P --

    @property
    def params(self) -> dict:
        """ 
        Returns all the parameters
        
        :return: The parameters
        :rtype: `dict`
        """
        
        specs = self.data["specs"]
        for k in specs:
            if not k in self.data["params"]:
                default = specs[k].get("default", None)
                if default:
                    self.set_param(k,default)
            
        return self.data["params"]
    
    def param_exists(self, name: str) -> bool:
        """ 
        Test if a parameter exists
        
        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """
        
        return name in self.data.get("specs",{})
    
    # -- R --

    # -- S --

    def set_param(self, name: str, value: [str, int, float, bool]):
        """ 
        Sets the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter (base type)
        :type: [str, int, float, bool, NoneType]
        """

        from gws.validator import Validator

        if not name in self.specs:
            raise Error("gws.model.Config", "set_param", f"Parameter '{name}' does not exist.")
        
        #param_t = self.specs[name]["type"]

        try:
            validator = Validator.from_specs(**self.specs[name])
            value = validator.validate(value)
        except Exception as err:
            raise Error("gws.model.Config", "set_param", f"Invalid parameter value '{name}'. Error message: {err}")
        
        self.data["params"][name] = value

    def set_params(self, params: dict):
        for k in params:
            self.set_param(k, params[k])

    @property
    def specs(self) -> dict:
        """ 
        Returns specs
        """
        return self.data["specs"]

    def set_specs(self, specs: dict):
        """ 
        Sets the specs of the config (remove current parameters)

        :param specs: The config specs
        :type: dict
        """
        if not isinstance(specs, dict):
            raise Error("gws.model.Config", "set_specs", f"The specs must be a dictionary.")
        
        if not self.id is None:
            raise Error("gws.model.Config", "set_specs", f"Cannot alter the specs of a saved config")
        
        self.data = {
            "specs" : specs,
            "params" : {}
        }
    
    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(shallow=shallow,**kwargs)
        if shallow:
            del _json["data"]
            
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
# ####################################################################
#
# ProgressBar class
#
# ####################################################################

class ProgressBar(Model):
    _min_allowed_delta_time = 1.0
    _min_value = 0.0
    
    _is_removable = False
    _table_name = "gws_progress_bar"
    _max_message_stack_length = 64
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.id:
            self.data = {
                "value": 0.0,
                "max_value": 0.0,
                "average_speed": 0.0,
                "start_time": 0.0,
                "current_time": 0.0,
                "elapsed_time": 0.0,
                "remaining_time": 0.0,
                "messages": [],
            }
            self.save()
    
    # -- A --
    
    def _add_message(self, message="Experiment under progress ..."):
        dtime = jsonable_encoder(datetime.now())
        self.data["messages"].append( f"{dtime}:: {message}" )
        
        if len(self.data["messages"]) > self._max_message_stack_length:
            self.data["messages"].pop(0)
    
    # -- C --
    
    def _compute_remaining_seconds(self):
        nb_remaining_steps = self.data["max_value"] - self.data["value"]
        if self.data["average_speed"] > 0.0:
            nb_remaining_seconds = nb_remaining_steps / self.data["average_speed"]
            return nb_remaining_seconds
        else:
            return -1
    
    # -- G --
    
    def get_max_value(self) -> float:
        return self.data["max_value"]
    
    # -- I --
    
    @property
    def is_initialized(self):
        return self.data["max_value"] > 0.0
    
    @property
    def is_running(self):
        return  self.is_initialized and \
                self.data["value"] > 0.0 and \
                self.data["value"] < self.data["max_value"]
    
    @property
    def is_finished(self):
        return  self.is_initialized and \
                self.data["value"] >= self.data["max_value"]
    
    # -- S --
    
    def start(self, max_value: float = 100.0):
        if max_value <= 0.0:
            raise Error("ProgressBar", "start", "Invalid max value")
    
        if self.data["start_time"] > 0.0:
            raise Error("ProgressBar", "start", "The progress bar has already started")
        
        self.data["max_value"] = max_value
        self.data["start_time"] = time.perf_counter()
        self._add_message(message="Experiment started")
        self.save()
    
    def stop(self, message="End of experiment!"):
        _max = self.data["max_value"]
        
        if self.data["value"] < _max:
            self.set_value(_max, message)

        self.data["remaining_time"] = 0.0
        self.save()
        
    def set_value(self, value: float, message="Experiment under progress ..."):
        """
        Increment the progress-bar value
        """
        
        _max = self.data["max_value"]        
        if _max == 0.0:
            self.start()
            #raise Error("ProgressBar", "start", "The progress bar has not started")
            
        if value > _max:
            value = _max
        
        if value < self._min_value:
            value = self._min_value
        
        current_time = time.perf_counter()
        delta_time = current_time - self.data["current_time"]
        ignore_update = delta_time < self._min_allowed_delta_time and value < _max
        if ignore_update:
            return
        
        self.data["value"] = value
        self.data["current_time"] = current_time
        self.data["elapsed_time"] = current_time - self.data["start_time"]
        self.data["average_speed"] = self.data["value"] / self.data["elapsed_time"]
        self.data["remaining_time"] = self._compute_remaining_seconds()
        self._add_message(message)
        
        if self.data["value"] == _max:
            self.stop()
        else:
            self.save()
        
    def set_max_value(self, value: int):
        _max = self.data["max_value"]
        
        if self.data["value"] > 0:
            raise Error("ProgressBar", "set_max_value", "The progress bar has already started")
        
        if isinstance(_max, int):
            raise Error("ProgressBar", "set_max_value", "The max value must be an integer")
       
        if _max <= 0:
            raise Error("ProgressBar", "set_max_value", "The max value must be greater than zero")
           
        self.data["max_value"] = value
        self.save()
    
    

        
class Process(Viewable):
    """
    Process class.

    :property input_specs: The specs of the input
    :type input_specs: dict
    :property output_specs: The specs of the output
    :type output_specs: dict
    :property config_specs: The specs of the config
    :type config_specs: dict
    """
    
    protocol_id = IntegerField(null=True, index=True)
    experiment_id = IntegerField(null=True, index=True)
    instance_name = CharField(null=True, index=True)
        
    created_by = ForeignKeyField(User, null=False, index=True)
    config =  ForeignKeyField(Config, null=False, index=True, backref='processes')    
    progress_bar = ForeignKeyField(ProgressBar, null=True, backref='process')

    input_specs: dict = {}
    output_specs: dict = {}
    config_specs: dict = {}
    
    is_instance_running = False
    is_instance_finished = False
    
    _experiment: 'Experiment' = None
    _protocol: 'Protocol' = None
    _file_store: 'FileStore' = None
    _input: Input = None
    _output: Output = None
    _max_progress_value = 100.0
    _is_singleton = False
    _is_removable = False
    _is_plug = False
    _table_name = 'gws_process'

    def __init__(self, *args, user=None, **kwargs):
        """
        Constructor     
        """
        
        super().__init__(*args, **kwargs)
        
        self._input = Input(self)
        self._output = Output(self)

        if self.input_specs is None:
            self.input_specs = {}
        
        if self.output_specs is None:
            self.output_specs = {}
        
        if self.config_specs is None:
            self.config_specs = {}
            
        self._init_io()
   
        if not self.title:
            self.data["title"] = kwargs.get('title', self.full_classname())
        
        if not self.title:
            self.data["title"] = kwargs.get('title', self.full_classname())
        
        if not self.id:
            self.config = Config(specs=self.config_specs)
            self.config.save()
        
            self.progress_bar = ProgressBar()
            self.progress_bar.save()

            if not user:
                user = User.get_sysuser()            
            
            if not isinstance(user, User):
                raise Error("gws.model.Process", "__init__", "The user must be an instance of User")
                
            self.created_by = user
        
        if not self.instance_name:
            self.instance_name = self.uri
            
        self.save()
    

    def _init_io(self):
        from .service.model_service import ModelService
        
        if type(self) is Process:
            # Is the Base (Abstract) Process object => cannot set io
            return
            
        # intput
        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        if not self.data.get("input"):
            self.data["input"] = {}

        for k in self.data["input"]:
            uri = self.data["input"][k]["uri"]
            type_ = self.data["input"][k]["type"]
            t = ModelService.get_model_type(type_)
            self._input.__setitem_without_check__(k, t.get(t.uri == uri))

        # output
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        if not self.data.get("output"):
            self.data["output"] = {}

        for k in self.data["output"]:
            uri = self.data["output"][k]["uri"]
            type_ = self.data["output"][k]["type"]
            t = ModelService.get_model_type(type_)
            self._output.__setitem_without_check__(k, t.get(t.uri == uri))
        
    # -- A --
    
    def archive(self, tf, archive_resources=True):
        """
        Archive the resource
        """
        
        if self.is_archived == tf:
            return True
        
        with DbManager.db.atomic() as transaction:
            try:
                if not super().archive(tf):
                    return False

                self.config.archive(tf) #-> try to archive the config if possible!

                if archive_resources:
                    for r in self.resources:
                        if not r.archive(tf):
                            transaction.rollback()
                            return False
            except Exception as err:
                Warning(err)
                transaction.rollback()
                return False
                    
        return True
    
    # -- C --
    
    @classmethod
    def create_process_type(cls):
        from gws.typing import ProcessType
        exist = ProcessType.select().where(ProcessType.ptype == cls.full_classname()).count()
        if not exist:
            pt = ProcessType(ptype = cls.full_classname())
            if issubclass(cls, Protocol):
                pt.base_ptype = "gws.model.Protocol"
            else:
                pt.base_ptype = "gws.model.Process"  
            pt.save()
            
    def create_experiment(self, study: 'Study', uri:str=None, user: 'User' = None):
        """
        Create an experiment using a protocol composed of this process
        
        :param study: The study in which the experiment is realized
        :type study: `gws.model.Study`
        :param study: The configuration of protocol
        :type study: `gws.model.Config`
        :return: The experiment
        :rtype: `gws.model.Experiment`
        """
        
        from .service.user_service import UserService
        
        proto = Protocol(processes={ 
            self.instance_name: self 
        })
        
        if user is None:
            user = UserService.get_current_user()
            if user is None:
                raise Error("Process", "create_experiment", "A user is required")
        
        if uri:
            e = Experiment(uri=uri, protocol=proto, study=study, user=user)
        else:
            e = Experiment(protocol=proto, study=study, user=user)
            
        e.save()
        return e
        
    @classmethod
    def create_table(cls, *args, **kwargs):
        if not Config.table_exists():
            Config.create_table()
            
        if not ProgressBar.table_exists():
            ProgressBar.create_table()
            
        if not Experiment.table_exists():
            Experiment.create_table()
 
        super().create_table(*args, **kwargs)

    def create_source_zip(self):
        from .service.model_service import ModelService

        model_t = ModelService.get_model_type(self.type) #/:\ Use the true object type (self.type)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())
    
    # -- D --
    
    def disconnect(self):
        """
        Disconnect the input and output ports
        """
        
        self._input.disconnect()
        self._output.disconnect()
            
    # -- E --
    
    @property
    def experiment(self):
        if self._experiment:
            return self._experiment
        
        if self.experiment_id:
            self._experiment = Experiment.get_by_id(self.experiment_id)
 
        return self._experiment
    
    # -- G -- 
    
    def get_param(self, name: str) -> [str, int, float, bool]:
        """
        Returns the value of a parameter of the process config by its name.

        :return: The paremter value
        :rtype: [str, int, float, bool]
        """
        
        return self.config.get_param(name)

    def get_next_procs(self) -> list:
        """ 
        Returns the list of (right-hand side) processes connected to the IO ports.

        :return: List of processes
        :rtype: list
        """
        
        return self._output.get_next_procs()

    # -- H --

    # -- I --
    
    @property
    def is_running(self) -> bool:
        if not self.progress_bar:
            return False
        
        p = ProgressBar.get_by_id(self.progress_bar.id)
        return p.is_running
    
    
    @property
    def is_finished(self) -> bool:
        if not self.progress_bar:
            return False
        
        p = ProgressBar.get_by_id(self.progress_bar.id)
        return p.is_finished
    
    @property
    def is_ready(self) -> bool:
        """
        Returns True if the process is ready (i.e. all its ports are 
        ready or it has never been run before), False otherwise.

        :return: True if the process is ready, False otherwise.
        :rtype: bool
        """
        
        return (not self.is_instance_running and not self.is_instance_finished) and self._input.is_ready 
    
    @property
    def input(self) -> 'Input':
        """
        Returns input of the process.

        :return: The input
        :rtype: Input
        """
        
        from .service.model_service import ModelService
        
        if self._input.is_empty:
            for k in self.data["input"]:
                uri = self.data["input"][k]["uri"]
                type_ = self.data["input"][k]["type"]
                t = ModelService.get_model_type(type_)
                self._input[k] = t.get(t.uri == uri)
            
        return self._input

    def in_port(self, name: str) -> InPort:
        """
        Returns the port of the input by its name.

        :return: The port
        :rtype: InPort
        """
        if not isinstance(name, str):
            raise Error("gws.model.Process", "in_port", "The name of the input port must be a string")
        
        if not name in self._input._ports:
            raise Error("gws.model.Process", "in_port", f"The input port '{name}' is not found")

        return self._input._ports[name]
    
    # -- J --

    # -- L --

    def __lshift__(self, name: str) -> InPort:
        """
        Alias of :meth:`in_port`.
        Returns the port of the input by its name

        :return: The port
        :rtype: InPort
        """
        return self.in_port(name)

    # -- O --

    @property
    def output(self) -> 'Output':
        """
        Returns output of the process.

        :return: The output
        :rtype: Output
        """
        
        from .service.model_service import ModelService
        
        if self._output.is_empty:
            for k in self.data["output"]:
                uri = self.data["output"][k]
                type_ = self.data["output"][k]["type"]
                t = ModelService.get_model_type(type_)
                self._output[k] = t.get(t.uri == uri)
                
        return self._output

    def out_port(self, name: str) -> OutPort:
        """
        Returns the port of the output by its name.

        :return: The port
        :rtype: OutPort
        """
        if not isinstance(name, str):
            raise Error("gws.model.Process", "out_port", "The name of the output port must be a string")
        
        if not name in self._output._ports:
            raise Error("gws.model.Process", "out_port", f"The output port '{name}' is not found")

        return self._output._ports[name]

    # -- P --
    
    def param_exists(self, name: str) -> bool:
        """ 
        Test if a parameter exists
        
        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """
        
        return self.config.param_exists(name)
    
    @property
    def protocol(self):
        if self._protocol:
            return self._protocol
        
        if self.protocol_id:
            self._protocol = Protocol.get_by_id(self.protocol_id)
            
        return self._protocol
    
    # -- R -- 
    
    @property
    def resources(self):
        Qrel = ProcessResource.select().where(ProcessResource.process_id == self.id)
        Q = []
        for o in Qrel:
            Q.append(o.resource)
            
        return Q
    
    async def _run(self):
        """ 
        Runs the process and save its state in the database.
        """
        
        if not self.is_ready:
            return
        
        try:
            await self._run_before_task()
            await self.task()
            await self._run_after_task()
        except Exception as err:
            self.progress_bar.stop(message = str(err))
            raise err
            
    async def _run_next_processes(self):
        self._output.propagate()
        aws  = []
        for proc in self._output.get_next_procs():
            aws.append( proc._run() )

        if len(aws):
            await asyncio.gather( *aws )
                
    async def _run_before_task( self, *args, **kwargs ):
        title = self.get_title()
        if title:
            Info(f"Running {self.full_classname()} '{title}' ...")
        else:
            Info(f"Running {self.full_classname()} ...")
        
        self.is_instance_running = True
        self.is_instance_finished = False
        
        self.data["input"] = {}
        for k in self._input:
            if self._input[k]:  #-> check that an input resource exists (for optional input)
                if not self._input[k].is_saved():
                    self._input[k].save()
                    
                self.data["input"][k] = {
                    "uri": self._input[k].uri,
                    "type": self._input[k].type
                }
            
        self.progress_bar.start(max_value=self._max_progress_value)
        self.save()
        
    async def _run_after_task( self, *args, **kwargs ):
        if self.get_title():
            Info(f"Task of {self.full_classname()} '{self.get_title()}' successfully finished!")
        else:
            Info(f"Task of {self.full_classname()} successfully finished!")
        
        self.is_instance_running = False
        self.is_instance_finished = True
        self.progress_bar.stop()

        if not self._is_plug:
            res = self.output.get_resources()
            for k in res:
                if not res[k] is None:
                    res[k].experiment = self.experiment
                    res[k].process = self
                    res[k].save()
        
        if not self._output.is_ready:
            return

        if isinstance(self, Protocol):
            self.save(update_graph=True)
        
        self.data["output"] = {}
        for k in self._output:
            if self._output[k]:  #-> check that an output resource exists (for optional outputs)
                self.data["output"][k] = {
                    "uri": self._output[k].uri,
                    "type": self._output[k].type
                }
            
        await self._run_next_processes()
        
    def __rshift__(self, name: str) -> OutPort:
        """ 
        Alias of :meth:`out_port`.
        
        Returns the port of the output by its name
        :return: The port
        :rtype: OutPort
        """
        return self.out_port(name)     
        
    # -- S --
     
    def set_experiment(self, experiment):

        if not isinstance(experiment, Experiment):
            raise Error("gws.model.Process", "set_experiment", f"An instance of Experiment is required")
        
        if not experiment.id:
            if not experiment.save():
                raise Error("gws.model.Process", "set_experiment", f"Cannot save the experiment")

        if self.experiment_id and self.experiment_id != experiment.id:
            raise Error("gws.model.Process", "set_experiment", f"The protocol is already related to an experiment")
            
        self.experiment_id = experiment.id        
        self.save()
            
    def set_input(self, name: str, resource: 'Resource'):
        """ 
        Sets the resource of an input port by its name.

        :param name: The name of the input port 
        :type name: str
        :param resource: A reources to assign to the port
        :type resource: Resource
        """
        if not isinstance(name, str):
            raise Error("gws.model.Process", "set_input", "The name must be a string.")
        
        if not isinstance(resource, Resource):
            raise Error("gws.model.Process", "set_input", "The resource must be an instance of Resource.")

        self._input[name] = resource
        
    def set_config(self, config: 'Config'):
        """ 
        Sets the config of the process.

        :param config: A config to assign
        :type config: Config
        """
        
        self.config = config
        self.save()

    def set_param(self, name: str, value: [str, int, float, bool]):
        """ 
        Sets the value of a config parameter.

        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """

        self.config.set_param(name, value)
        self.config.save()

    # -- T --

    async def task(self):
        pass
        
    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)

        del _json["experiment_id"]
        del _json["protocol_id"]
        
        if "input" in _json["data"]:
            del _json["data"]["input"]
            
        if "output" in _json["data"]:
            del _json["data"]["output"]
            
        bare = kwargs.get("bare")
        if bare:
            _json["experiment"] = { "uri" : "" }
            _json["protocol"] = { "uri" : "" }
        else:
            e_uri = None
            if self.experiment_id:
                e_uri = self.experiment.uri

            p_uri = None
            if self.protocol_id:
                p_uri = self.protocol.uri

            _json["experiment"] = { "uri" : e_uri }
            _json["protocol"] = { "uri" : p_uri }
        
        if shallow:
            _json["config"] = { "uri" : self.config.uri }
            
            if _json["data"].get("graph"):
                del _json["data"]["graph"]
        else:
            _json["config"] = self.config.to_json(**kwargs)
            
        _json["input"] = self.input.to_json(**kwargs)
        _json["output"] = self.output.to_json(**kwargs)
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
# ####################################################################
#
# Protocol class
#
# ####################################################################

class Protocol(Process):
    """ 
    Protocol class.

    :property processes: Dictionnary of processes
    :type processes: dict
    :property connectors: List of connectors represinting process connection
    :type connectors: list
    """

    _is_singleton = False
    _processes: dict = {}
    _connectors: list = []
    _interfaces: dict = {}
    _outerfaces: dict = {}
    _defaultPosition: list = [0.0, 0.0]
    
    #_table_name = "gws_protocol"
    
    def __init__(self, *args, processes: dict = {}, \
                 connectors: list = [], interfaces: dict = {}, outerfaces: dict = {}, \
                 user = None, **kwargs):
        
        super().__init__(*args, user = user, **kwargs)

        self._processes = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}
        self._defaultPosition = [0.0, 0.0]
        
        if self.uri and self.data.get("graph"):          #the protocol was saved in the super-class
            self._build_from_dump( self.data["graph"], title=self.title)
        else:
            if not isinstance(processes, dict):
                raise Error("gws.model.Protocol", "__init__", "A dictionnary of processes is expected")

            if not isinstance(connectors, list):
                raise Error("gws.model.Protocol", "__init__", "A list of connectors is expected")

            # set process
            for name in processes:
                proc = processes[name]
                if not isinstance(proc, Process):
                    raise Error("gws.model.Protocol", "__init__", "The dictionnary of processes must contain instances of Process")

                self.add_process(name, proc)

            # set connectors
            for conn in connectors:
                if not isinstance(conn, Connector):
                    raise Error("gws.model.Protocol", "__init__", "The list of connector must contain instances of Connectors")

                self.add_connector(conn)

            if user is None:
                try:
                    from .service.user_service import UserService
                    user = UserService.get_current_user()
                except:
                    raise Error("gws.model.Protocol", "__init__", "A user is required")

            if isinstance(user, User):
                if self.created_by.is_sysuser:
                    # The sysuser is used by default to create any Process
                    # We therefore replace the syssuser by the currently authenticated user

                    if user.is_authenticated:
                        self.create_by = user 
                    else:
                        raise Error("gws.model.Protocol", "__init__", "The user must be authenticated")
            else:
                raise Error("gws.model.Protocol", "__init__", "The user must be an instance of User")

            # set interfaces
            self.__set_interfaces(interfaces)
            self.__set_outerfaces(outerfaces)
            self.data["graph"] = self.dumps(as_dict=True)
            self.save()   #<- will save the graph
    
    def _init_io(self):
        pass
    
    # -- A --

    def add_process(self, name: str, process: Process):
        """ 
        Adds a process to the protocol.

        :param name: Unique name of the process
        :type name: str
        :param process: The process
        :type process: Process
        """

        if not self.id:
            self.save()
            
        if self.is_instance_finished or self.is_instance_running:
            raise Error("gws.model.Protocol", "add_process", "The protocol has already been run")
       
        if not isinstance(process, Process):
            raise Error("gws.model.Protocol", "add_process", f"The process '{name}' must be an instance of Process")

        if process.protocol_id and self.id != process.protocol_id:
            raise Error("gws.model.Protocol", "add_process", f"The process instance '{name}' already belongs to another protocol")
        
        if name in self._processes:
            raise Error("gws.model.Protocol", "add_process", f"Process name '{name}' already exists")
        
        if process in self._processes.items():
            raise Error("gws.model.Protocol", "add_process", f"Process '{name}' duplicate")

        process.protocol_id = self.id
        process._protocol = self
        
        if self.experiment_id:
            process.set_experiment(self.experiment)

        process.instance_name = name
        process.save()
        
        self._processes[name] = process

    def add_connector(self, connector: Connector):
        """ 
        Adds a connector to the protocol.

        :param connector: The connector
        :type connector: Connector
        """

        if self.is_instance_finished or self.is_instance_running:
            raise Error("gws.model.Protocol", "add_connector", "The protocol has already been run")
        
        if not isinstance(connector, Connector):
            raise Error("gws.model.Protocol", "add_connector", "The connector must be an instance of Connector")
        
        if  not connector.left_process in self._processes.values() or \
            not connector.right_process in self._processes.values():
            raise Error("gws.model.Protocol", "add_connector", "The processes of the connector must belong to the protocol")
        
        if connector in self._connectors:
            raise Error("gws.model.Protocol", "add_connector", "Duplciated connector")

        self._connectors.append(connector)
    
    # -- B --
    
    def _build_from_dump( self, graph: (str, dict), title=None, rebuild = False ) -> 'Protocol':
        """ 
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """
        
        from .service.model_service import ModelService
        
        if isinstance(graph, str):
            graph = json.loads(graph)
        
        if not isinstance(graph,dict):
            return
        
        if not isinstance(graph.get("nodes"), dict) or not graph["nodes"]:
            return
        
        if not title:
            title = graph.get("title", self.full_classname())

        if not self.title or self.title == self.full_classname():
            self.set_title(title)
        
        if rebuild:
            if self.experiment.is_draft:
                deleted_keys = []
                for k in self._processes:
                    proc = self._processes[k]

                    is_removed = False
                    if k in graph["nodes"]:
                        if proc.type != graph["nodes"][k].get("type"):
                            is_removed = True
                    else:
                        is_removed = True

                    if is_removed:
                        proc.delete_instance()
                        deleted_keys.append(k)
                    
                    # disconnect the port to prevent connection errors later
                    proc.disconnect()
                    
                for k in deleted_keys:
                    del self._processes[k]
                
        # will be rebuilt
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}
            
        # create nodes
        for k in graph["nodes"]:
            node_json = graph["nodes"][k]
            proc_uri = node_json.get("uri",None)
            proc_type_str = node_json["type"]
            
            try:
                proc_t = ModelService.get_model_type(proc_type_str)
                
                if proc_t is None:
                    raise Exception(f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")
                else:
                    if proc_uri:
                        proc = proc_t.get(proc_t.uri == proc_uri)
                    else:
                        if issubclass(proc_t, Protocol):
                            proc = Protocol.from_graph( node_json["data"]["graph"] )
                        else:
                            proc = proc_t()
                    
                    if not k in self._processes:
                        self.add_process( k, proc )
                
                # update config if required
                config = node_json.get("config")
                if config:
                    params = config.get("data",{}).get("params",{})
                    proc.config.set_params(params)
                    proc.config.save()
                
            except Exception as err:
                raise Error("gws.model.Protocol", "_build_from_dump", f"An error occured. Error: {err}")
        
        # create interfaces and outerfaces
        interfaces = {}
        outerfaces = {}
        for k in graph["interfaces"]:
            _to = graph["interfaces"][k]["to"]  #destination port of the interface
            proc_name = _to["node"]
            port_name = _to["port"]
            proc = self._processes[proc_name]
            port = proc.input.ports[port_name]
            interfaces[k] = port

        for k in graph["outerfaces"]:
            _from = graph["outerfaces"][k]["from"]  #source port of the outerface
            proc_name = _from["node"]
            port_name = _from["port"]
            proc = self._processes[proc_name]
            port = proc.output.ports[port_name]
            outerfaces[k] = port
            
        self.__set_interfaces(interfaces)
        self.__set_outerfaces(outerfaces)
        
        # create links
        for link in graph["links"]:
            proc_name = link["from"]["node"]
            lhs_port_name = link["from"]["port"]
            lhs_proc = self._processes[proc_name]

            proc_name = link["to"]["node"]
            rhs_port_name = link["to"]["port"]
            rhs_proc = self._processes[proc_name]

            connector = (lhs_proc>>lhs_port_name | rhs_proc<<rhs_port_name)
            self.add_connector(connector)
        
        self.save(update_graph=True)
        
    # -- C --

    def create_experiment(self, study: 'Study', user: 'User'=None):
        """
        Realize a protocol by creating a experiment
        
        :param study: The study in which the protocol is realized
        :type study: `gws.model.Study`
        :param config: The configuration of protocol
        :type config: `gws.model.Config`
        :return: The experiment
        :rtype: `gws.model.Experiment`
        """
   
        if user is None:
            from .service.user_service import UserService
            user = UserService.get_current_user()
            if user is None:
                raise Error("Process", "create_experiment", "A user is required")
                
       
        e = Experiment(user=user, study=study, protocol=self)

        e.save()
        
        return e

    def create_source_zip(self):
        graph = self.dumps()
        return zlib.compress(graph.encode())

    @classmethod
    def create_table(cls, *args, **kwargs):
        if not Experiment.table_exists():
            Experiment.create_table()
        
        if not Config.table_exists():
            Config.create_table()

        super().create_table(*args, **kwargs)

    # -- D -- 

    def disconnect(self):
        """
        Disconnect the input, output, interfaces and outerfaces
        """
        
        super().disconnect()
        
        for k in self._interfaces:
            self._interfaces[k].disconnect()
            
        for k in self._outerfaces:
            self._outerfaces[k].disconnect()
        
    def dumps( self, as_dict: bool = False, prettify: bool = False, bare: bool = False ) -> str:
        """ 
        Dumps the JSON graph representing the protocol.
        
        :param as_dict: If True, returns a dictionnary. A JSON string is returns otherwise.
        :type as_dict: bool
        :param prettify: If True, the JSON string is indented.
        :type prettify: bool
        :param bare: If True, returns a bare dump i.e. the uris of the processes (and sub-protocols) of not returned. Bare dumps allow creating a new protocols from scratch.
        :type bare: bool
        """

        graph = dict(
            title = self.get_title(),
            uri = ("" if bare else self.uri),
            nodes = {},
            links = [],
            interfaces = {},
            outerfaces = {},
        )

        for conn in self._connectors:
            link = conn.to_json(bare=bare)
            graph['links'].append(link)
        
        for k in self._processes:
            proc = self._processes[k]
            graph["nodes"][k] = proc.to_json(bare=bare)

        for k in self._interfaces:
            graph['interfaces'][k] = self._interfaces[k].to_json(bare=bare)

        for k in self._outerfaces:
            graph['outerfaces'][k] = self._outerfaces[k].to_json(bare=bare)

        graph["layout"] = self.get_layout()
        
        if as_dict:
            return graph
        else:
            if prettify:
                return json.dumps(graph, indent=4)
            else:
                return json.dumps(graph)
    
    # -- F --
    
    @classmethod
    def from_graph( cls, graph: dict ) -> 'Protocol':
        """ 
        Create a new instance from a existing graph

        :return: The protocol
        :rtype": Protocol
        """
        
        if isinstance(graph, str):
            graph = json.loads(graph)
            
        if graph.get("uri"):
            proto = Protocol.get(Protocol.uri == graph.get("uri"))
        else:
            proto = Protocol()
            proto._build_from_dump(graph)
            proto.data["graph"] = proto.dumps(as_dict=True)
            proto.save()
            
        return proto
    
    # -- G --
    
    @property
    def graph(self):
        return self.data.get("graph",{})
    
    def get_process(self, name: str) -> Process:
        """ 
        Returns a process by its name.

        :return: The process
        :rtype": Process
        """
        return self._processes[name]
    
    def get_layout(self):
        return self.data.get("layout", {})
    
    def get_process_position(self, name: str):
        positions = self.get_layout()
        return positions.get(name, self._defaultPosition)

    def get_interface_of_inport(self, inport: InPort) -> Interface:
        """ 
        Returns interface with a given target input port
        
        :param inport: The InPort
        :type inport: InPort
        :return: The interface, None otherwise
        :rtype": Interface
        """
        
        for k in self._interfaces:
            port = self._interfaces[k].target_port
            if port is inport:
                return self._interfaces[k]

        return None
    
    def get_outerface_of_outport(self, outport: OutPort) -> Outerface:
        """ 
        Returns interface with a given target output port
        
        :param outport: The InPort
        :type outport: OutPort
        :return: The outerface, None otherwise
        :rtype": Outerface
        """
        
        for k in self._outerfaces:
            port = self._outerfacess[k].source_port
            if port is outport:
                return self._outerfacess[k]

        return None
    
    # -- I --

    def is_child(self, process: Process) -> bool:
        """ 
        Returns True if the process is in the Protocol, False otherwise.

        :param process: The process
        :type process: Process
        :return: True if the process is in the Protocol, False otherwise
        :rtype: bool
        """
        return process in self._processes.values()
    
    def is_interfaced_with(self, process: Process) -> bool:
        """ 
        Returns True if the input poort the process is an interface of the protocol
        """
        
        for k in self._interfaces:
            port = self._interfaces[k].target_port
            if process is port.parent.parent:
                return True

        return False

    def is_outerfaced_with(self, process: Process) -> bool:
        """ 
        Returns True if the input poort the process is an outerface of the protocol
        """
        for k in self._outerfaces:
            port = self._outerfaces[k].source_port
            if process is port.parent.parent:
                return True

        return False

    # -- L --
    
    # -- P --
    
    # -- R --
    
    async def _run_before_task(self, *args, **kwargs):
        self.save()
        
        if self.is_running or self.is_finished:
            return
        
        self._set_inputs()

        if not self.experiment:
            raise Error("gws.model.Protocol", "_run_before_task", "No experiment defined")

        await super()._run_before_task(*args, **kwargs)
        
    async def task(self):
        """ 
        BUILT-IN PROTOCOL TASK
        
        Runs the process and save its state in the database.
        Override mother class method.
        """
        
        sources = []
        for k in self._processes:
            proc = self._processes[k]
            if proc.is_ready or self.is_interfaced_with(proc):
                sources.append(proc)
        
        aws = []
        for proc in sources:
            aws.append( proc._run() )
        
        if len(aws):
            await asyncio.gather(*aws)

    async def _run_after_task(self, *args, **kwargs):
        if self.is_finished:
            return
        
        # Exit the function if an inner process has not yet finished!
        for k in self._processes:
            if not self._processes[k].is_finished:
                return

        # Good! The protocol task is finished!
        self._set_outputs()
        await super()._run_after_task(*args, **kwargs)
 
    # -- S --
    
    def save(self, *args, update_graph=False, **kwargs):
        with DbManager.db.atomic() as transaction:
            try:
                for k in self._processes:
                    self._processes[k].save()

                if not self.is_saved():
                    Activity.add(
                        Activity.CREATE,
                        object_type = self.full_classname(),
                        object_uri = self.uri
                    )
                
                if update_graph:
                     self.data["graph"] = self.dumps(as_dict=True)
                        
                return super().save(*args, **kwargs)
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Protocol", "save", f"Could not save the protocol. Error: {err}")
    
    
    def set_experiment(self, experiment):
        super().set_experiment(experiment)
        for k in self._processes:
            self._processes[k].set_experiment(experiment)
            self._processes[k].save()
        
    def set_title(self, title):
        super().set_title(title)
        self.graph["title"] = title
    
    def set_layout(self, layout: dict):
        self.data["layout"] = layout
    
    def _set_inputs(self, *args, **kwargs):
        """
        Propagate resources through interfaces
        """
        
        for k in self._interfaces:
            port = self._interfaces[k].target_port
            port.resource = self.input[k]

    def _set_outputs(self, *args, **kwargs):
        """
        Propagate resources through outerfaces
        """
        
        for k in self._outerfaces:
            port = self._outerfaces[k].source_port
            self.output[k] = port.resource

    def __set_input_specs(self, input_specs):
        self.input_specs = input_specs
        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        #self.data['input_specs'] = self._input.get_specs()

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        #self.data['output_specs'] = self._output.get_specs()

    def __set_interfaces(self, interfaces: dict):
        from .service.model_service import ModelService
        
        input_specs = {}
        for k in interfaces:
            input_specs[k] = interfaces[k]._resource_types

        self.__set_input_specs(input_specs)
        
        if not self.input_specs:
            return
        
        self._interfaces = {}
        for k in interfaces:
            source_port = self.input.ports[k]
            self._interfaces[k] = Interface(name=k, source_port=source_port, target_port=interfaces[k])
        
        if self.data.get("input"):
            for k in self.data.get("input"):
                uri = self.data["input"][k]["uri"]
                type_ = self.data["input"][k]["type"]
                t = ModelService.get_model_type(type_)
                self.input.__setitem_without_check__(k, t.get(t.uri == uri) )

    def __set_outerfaces(self, outerfaces: dict):
        from .service.model_service import ModelService
        
        output_specs = {}
        for k in outerfaces:
            output_specs[k] = outerfaces[k]._resource_types

        self.__set_output_specs(output_specs)
        
        if not self.output_specs:
            return
        
        self._outerfaces = {}
        for k in outerfaces:
            target_port = self.output.ports[k]
            try:
                self._outerfaces[k] = Outerface(name=k, target_port=target_port, source_port=outerfaces[k])  
            except:
                pass

        if self.data.get("output"):
            for k in self.data["output"]:
                uri = self.data["output"][k]["uri"]
                type_ = self.data["output"][k]["type"]
                t = ModelService.get_model_type(type_)
                self.output.__setitem_without_check__(k, t.get(t.uri == uri) )

    # -- T --
    
    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(shallow=shallow, **kwargs)
        
        if shallow:
            if _json["data"].get("graph"):
                del _json["data"]["graph"]
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
# ####################################################################
#
# Study class
#
# ####################################################################

class Study(Viewable):
    """
    Study class.
    """
    
    _table_name = 'gws_study'
    
    def archive(self, tf:bool)->bool:
        """
        Deactivated method. Returns False.
        """
        
        return False
    
    @classmethod
    def create_default_instance( cls ):
        """
        Create the default study of the lab
        """
        
        cls.get_default_instance()
    
    @classmethod
    def get_default_instance( cls ):
        """
        Get the default study of the lab
        """
        
        try:
            study = Study.get_by_id(1)
        except:
            study = Study(
                data = {
                    "title": "Default study",
                    "description": "The default study of the lab"
                }
            )
            study.save()
        
        return study

# ####################################################################
#
# Experiment class
#
# ####################################################################

class Experiment(Viewable):
    """
    Experiment class.
    
    :property origin: The original experiment used to create this experiment
    :type origin: `gws.model.Experiment`
    :property study: The study of the experiment
    :type study: `gws.model.Study`
    :property created_by: The user who created the experiment
    :type created_by: `gws.model.User`
    :property score: The score of the experiment
    :type score: `float`
    :property is_validated: True if the experiment is validated, False otherwise. Defaults to False.
    :type is_validated: `float`
    """
    origin = ForeignKeyField('self', null=True, backref='children') 
    study = ForeignKeyField(Study, null=True, backref='experiments')
    protocol_id = IntegerField(null=True, index=True)
    created_by = ForeignKeyField(User, null=True, backref='created_experiments')
    score = FloatField(null=True, index=True)    
    is_validated = BooleanField(default=False, index=True)
    
    _is_running = BooleanField(default=False, index=True)
    _is_finished = BooleanField(default=False, index=True)
    _is_success = BooleanField(default=False, index=True)
    
    _protocol = None
    _event_listener: EventListener = None
    _table_name = 'gws_experiment'

    def __init__(self, *args, protocol:'Protocol'=None, user:'User'=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.id:
            self.data["pid"] = 0
            if user is None:
                try:
                    from .service.user_service import UserService
                    user = UserService.get_current_user()
                except:
                    raise Error("gws.model.Experiment", "__init__", "An user is required")
                    
            if isinstance(user, User):
                if not user.is_authenticated:
                    raise Error("gws.model.Experiment", "__init__", "An authenticated user is required")
                
                self.created_by = user
            else:
                raise Error("gws.model.Experiment", "__init__", "The user must be an instance of User")
            
            if not self.save():
                raise Error("gws.model.Experiment", "__init__", "Cannot create experiment")
                
            # attach the protocol
            if protocol is None:
                protocol = Protocol(user=user)
            
            self._protocol = protocol
            protocol.set_experiment(self)
            self.protocol_id = protocol.id
            self.save()
            
        else:
            pass
            #self.protocol.set_experiment(self)
        
        self._event_listener = EventListener()
        
    # -- A --
    
    def add_report(self, report: 'Report'):
        report.experiment = self

    def archive(self, tf:bool, archive_resources=True):
        """
        Archive the experiment
        """
        
        if self.is_archived == tf:
            return True
        
        with DbManager.db.atomic() as transaction:
            try:
                Activity.add(
                    Activity.ARCHIVE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )
                
                for p in self.processes:
                    if not p.archive(tf, archive_resources=archive_resources):
                        transaction.rollback()
                        return False
                    
                if super().archive(tf):
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except Exception as err:
                Warning(err)
                transaction.rollback()
                return False

      
    # -- C --
        
    @classmethod
    def count_of_running_experiments(cls):
        """ 
        Returns the count of experiment in progress

        :return: The count of experiment in progress
        :rtype: `int`
        """
        
        return Experiment.select().where(Experiment.is_running == True).count()
    
    # -- F --

    # -- I --
    
    @property
    def is_finished(self) -> bool:
        if not self.id:
            return False
        
        e = Experiment.get_by_id(self.id)
        return e._is_finished
    
    @property
    def is_running(self) -> bool:
        if not self.id:
            return False
        
        e = Experiment.get_by_id(self.id)
        return e._is_running
    
    @property
    def is_draft(self) -> bool:
        """ 
        Returns True if the experiment is a draft, i.e. has nether been run and is not validated. False otherwise.

        :return: True if the experiment not running nor finished
        :rtype: `bool`
        """
        
        return (not self.is_validated) and (not self.is_running) and (not self.is_finished)

    @property
    def is_pid_alive(self) -> bool:
        if not self.pid:
            raise Error("Experiment", "is_pid_alive", f"No such process found")
        
        try:
            sproc = SysProc.from_pip(self.pid)
        except:
            raise Error("Experiment", "is_pid_alive", f"No such process found or its access is denied (pid = {self.pid})")
            
        sproc = SysProc.from_pip(self.pid)
        return sproc.is_alive()
    
    # -- J --

    # -- K --
    
    async def kill_pid(self):
        """ 
        Kill the experiment if it is running. 
        
        This is only possible if the experiment has been started through the cli. 
        """
        
        from .service.http_service import HTTPService
        
        if not HTTPService.is_http_context():
            raise Error("Experiment", "kill_pid", f"The user must be in http context")
            
        if self.pip:
            try:
                sproc = SysProc.from_pip(self.pid)
            except:
                raise Error("Experiment", "is_pid_alive", f"No such process found or its access is denied (pid = {self.pid})")
            
        try:
            sproc.terminate()
            sproc.wait()
        except:
            raise Error("Experiment", "kill", f"Cannot kill pid {self.pid}.")
        
        Activity.add(
            Activity.STOP,
            object_type = self.full_classname(),
            object_uri = self.uri
        )

        # Gracefully stop the experiment and exit!
        message = f"Experiment manullay stopped by a user."
        self.protocol.progress_bar.stop(message)
        self.data["pid"] = 0
        self._is_running = False
        self._is_finished = True
        self._is_success = False
        self.save()
            
    # -- O --

    def on_end(self, call_back: callable):
        self._event_listener.add("end", call_back)
    
    def on_start(self, call_back: callable):
        self._event_listener.add("start", call_back)
        
    # -- P --
    
    @property
    def pid(self):
        if not "pid" in self.data:
            return 0
        
        return self.data["pid"]
    
    @property
    def processes(self):
        if not self.id:
            return []
        
        return Process.select().where(Process.experiment_id == self.id)
    
    @property
    def protocol(self):
        if not self._protocol:
            self._protocol = Protocol.get(Protocol.id == self.protocol_id)
        
        return self._protocol
    
    # -- R --

    @property 
    def resources(self):
        #Q = Resource.select()\
        #            .where(Experiment.id == self.id) \
        #            .order_by(Resource.creation_datetime.desc())
        
        Qrel = ExperimentResource.select().where(ExperimentResource.experiment_id == self.id)
        Q = []
        for o in Qrel:
            Q.append(o.resource)
            
        return Q
      
    def run_through_cli(self, *, user=None):
        """ 
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.model.User`
        """

        from gws.system import SysProc
        from .service.user_service import UserService
        
        settings = Settings.retrieve()
        cwd_dir = settings.get_cwd()
        
        if not user:
            try:
                user = UserService.get_current_user()
            except:
                raise Error("gws.model.Experiment", "run_through_cli", "A user is required")
            
            if not user.is_authenticated:
                raise Error("gws.model.Experiment", "run_through_cli", "An authenticated user is required")
                    
        cmd = [
            "python3", 
             os.path.join(cwd_dir, "manage.py"), 
             "--cli", 
             "gws.cli.run_experiment",
             "--experiment-uri", self.uri,
             "--user-uri", user.uri
        ]
         
        if settings.is_test:
            cmd.append("--cli_test")
        
        sproc = SysProc.popen(cmd, stderr=DEVNULL, stdout=DEVNULL)
        self.data["pid"] = sproc.pid
        self.save()
        
    async def run(self, *, user=None, wait_response=False):
        """ 
        Run the experiment

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.model.User`
        :param wait_response: True to wait the response. False otherwise.
        :type wait_response: `bool`
        """
        
        if self.is_running or self.is_finished:
            return
        
        if wait_response:
            await self.__run(user=user)
        else:
            from .service.http_service import HTTPService
            if HTTPService.is_http_context():
                # run the experiment throug the cli to prevent blocking HTTP requests
                self.run_through_cli(user=user)
            else:
                await self.__run(user=user)
        
    async def __run(self, * ,user=None):
        """ 
        Run the experiment

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.model.User`
        """
        
        from .service.user_service import UserService
        
        if not user:
            try:
                user = UserService.get_current_user()
            except:
                raise Error("gws.model.Experiment", "run", "A user is required")

            if not user.is_authenticated:
                    raise Error("gws.model.Experiment", "run", "A authenticated user is required")

        if self.is_archived:
            raise Error("gws.model.Experiment", "run", f"The experiment is archived")

        if self.is_validated:
            raise Error("gws.model.Experiment", "run", f"The experiment is validated")

        Activity.add(
            Activity.START,
            object_type = self.full_classname(),
            object_uri = self.uri,
            user=user
        )

        try:
            self.protocol.set_experiment(self)
            self.data["pid"] = 0
            self._is_running = True
            self._is_finished = False
            self.save()

            if self._event_listener.exists("start"):
                self._event_listener.sync_call("start", self)
                await self._event_listener.async_call("start", self)

            await self.protocol._run()

            if self._event_listener.exists("end"):
                self._event_listener.sync_call("end", self)
                await self._event_listener.async_call("end", self)

            self.data["pid"] = 0
            self._is_running = False
            self._is_finished = True
            self._is_success = True
            self.save()
        except Exception as err:
            time.sleep(3)  #-> wait for 3 sec to prevent database lock!

            # Gracefully stop the experiment and exit!
            message = f"An error occured. Exception: {err}"
            self.protocol.progress_bar.stop(message)
            self.data["pid"] = 0
            self._is_running = False
            self._is_finished = True
            self._is_success = False
            self.save()
            raise Error("gws.model.Experiment", "run", f"An error occured. Exception: {err}")
                
    # -- S --

    def save(self, *args, **kwargs):  
        with DbManager.db.atomic() as transaction:
            try:
                if not self.is_saved():
                    Activity.add(
                        Activity.CREATE,
                        object_type = self.full_classname(),
                        object_uri = self.uri
                    )
        
                return super().save(*args, **kwargs)
            except:
                transaction.rollback()
                return False
    
    # -- T --
    
    def to_json(self, *, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json.update({
            "study": {"uri": self.study.uri},
            "protocol": {"uri": self.protocol.uri},
            "is_draft": self.is_draft,
            "is_running": self.is_running,
            "is_finished": self.is_finished,
            "is_success": self._is_success
        })
        
        if not _json["data"].get("title"):
            _json["data"]["title"] = self.protocol.title
        
        if not _json["data"].get("description"):
            _json["data"]["description"] = self.protocol.description
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json   
        
    # -- V --
    
    def validate(self, user: User):
        """
        Validate the experiment
        
        :param user: The user who validate the experiment
        :type user: `gws.model.User`
        """
        
        if self.is_validated:
            return
        
        with DbManager.db.atomic() as transaction:
            try:
                self.is_validated = True
                self.save()
                
                Activity.add(
                    Activity.VALIDATE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )
            except:
                transaction.rollback()
                raise Error("gws.model.Experiment", "save", f"Could not validate the experiment. Error: {err}")
    
# ####################################################################
#
# Resource class
#
# ####################################################################

class Resource(Viewable):
    """
    Resource class.
    
    :property process: The process that created he resource
    :type process: Process
    """
    
    #process = ForeignKeyField(Process, null=True, backref='+')
    #experiment = ForeignKeyField(Experiment, null=True, backref='+')

    _process = None
    _experiment = None
    
    _table_name = 'gws_resource'
    
    def __init__(self, *args, process: Process=None, experiment: Experiment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if process:
            self.process = process
        
        if experiment:
            self.experiment = experiment
    
    # -- C --
    
    @classmethod
    def create_resource_type(cls):
        from gws.typing import ResourceType
        exist = ResourceType.select().where(ResourceType.rtype == cls.full_classname()).count()
        if not exist:
            rt = ResourceType(rtype = cls.full_classname())
            rt.base_rtype = "gws.model.Resource"  
            rt.save()
            
    # -- D --

    @classmethod
    def drop_table(cls, *args, **kwargs):
        super().drop_table(*args, **kwargs)
        ProcessResource.drop_table()
        ExperimentResource.drop_table()
    
    # -- E --
    
    @property
    def experiment(self):
        if not self._experiment:        
            try:
                o = ExperimentResource.get( (resource == self)&(resource_type == self.type) )
                self._experiment = o.experiment
            except:
                return None
        
        return self._experiment
        
    @experiment.setter
    def experiment(self, experiment: Experiment):
        if self.experiment:
            return
        
        if not self.id:
            self.save()
            
        o = ExperimentResource(
            experiment_id=experiment.id, 
            resource_id=self.id,
            resource_type=self.type, 
        )
        o.save()
        self._experiment = experiment
        
    def _export(self, file_path: str, file_format:str = None):
        """ 
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """
        
        #@ToDo: ensure that this method is only called by an Exporter
        
        pass
    
    # -- G --

    # -- I --
    
    @classmethod
    def _import(cls, file_path: str, file_format:str = None) -> any:
        """ 
        Import a resource from a repository. Must be overloaded by the child class.

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype any
        """
        
        #@ToDo: ensure that this method is only called by an Importer 
        
        pass
    
    # -- J --
    
    @classmethod
    def _join(cls, *args, **params) -> 'Model':
        """ 
        Join several resources

        :param params: Joining parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Joiner
        
        pass
    
    # -- P --
    
    @property
    def process(self):
        if not self._process:   
            try:
                o = ProcessResource.get( (resource == self)&(resource_type == self.type) )
                self._process = o.process
            except:
                return None
        
        return self._process
    
    @process.setter
    def process(self, process: Process):
        if self.process:
            return
        
        if not self.id:
            self.save()
            
        o = ProcessResource(
            process_id=process.id, 
            resource_id=self.id,
            resource_type=self.type, 
        )
        o.save()
        self._process = process
    
    # -- R --
    
    # -- S --
    
    #def save(*args, **kwargs):
    #    with DbManager.db.atomic() as transaction:
    #        try:
    #            if self._process:
    #                self.process = self._process
    #
    #            if self._experiment:
    #                self.experiment = self._experiment
    #
    #            return super().save(*args, **kwargs)
    #        except:
    #            transaction.rollback()
    #            return False
        
            
    def _select(self, **params) -> 'Model':
        """ 
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Selector
        
        pass
    
    # -- T --
    
    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(shallow=shallow,**kwargs)

        if self.experiment:
            _json.update({
                "experiment": {"uri": self.experiment.uri},
                "process": {
                    "uri": self.process.uri,
                    "type": self.process.type,
                },
            })
        
        if shallow:
            del _json["data"]
            
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

class ExperimentResource(Model):
    experiment_id = IntegerField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_type = CharField(null=False, index=True)
    
    _table_name = "gws_experiment_resource"
    
    class Meta:
        indexes = (
            (("experiment_id", "resource_id", "resource_type"), True),
        )
    
    @property
    def resource(self):
        from .service.model_service import ModelService
        
        t = ModelService.get_model_type(self.resource_type)
        return t.get_by_id(self.resource_id)
    
    @property
    def experiment(self):
        return Experiment.get_by_id(self.experiment_id)
        
    
class ProcessResource(Model):
    process_id = IntegerField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_type = CharField(null=False, index=True)
    
    _table_name = "gws_process_resource"
    
    class Meta:
        indexes = (
            (("process_id", "resource_id", "resource_type"), True),
        )
        
    @property
    def resource(self):
        from .service.model_service import ModelService
        
        t = ModelService.get_model_type(self.resource_type)
        return t.get_by_id(self.resource_id)
    
    @property
    def process(self):
        return Process.get_by_id(self.experiment_id)
    
# ####################################################################
#
# ResourceSet class
#
# ####################################################################

class ResourceSet(Resource):
    
    _set: dict = None
    _resource_types = (Resource, )
    
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        if self.id is None:
            self.data["set"] = {}
            self._set = {}
        if self._set is None:
            self._set = {}
    
    # -- A --
    
    def add(self, val):
        if not isinstance(val, self._resource_types):
            raise Error("gws.model.ResourceSet", "__setitem__", f"The value must be an instance of {self._resource_types}. The actual value is a {type(val)}.")
        
        if not val.is_saved():
            val.save()
        self.set[val.uri] = val
            

    # -- C --
    
    def __contains__(self, val):
        return val in self.set
    
    # -- E --
    
    def exists( self, resource ) -> bool:
        return resource in self._set
    
    # -- G --
    
    def __getitem__(self, key):
        return self.set[key]
    
    # -- I --

    def __iter__(self):
        return self.set.__iter__()
    
    # -- L --
    
    def len(self):
        return self.len()
    
    def __len__(self):
        return len(self.set)
    
    # -- N --
    
    def __next__(self):
        return self.set.__next__()
    
    # -- R --
    
    def remove(self):
        with DbManager.db.atomic() as transaction:
            try:
                for k in self._set:
                    if not self._set.remove():
                        transaction.rollback()
                        return False

                if not super().remove():
                    transaction.rollback()
                    return False
                else:
                    return True
            except:
                transaction.rollback()
                return False
            
    # -- S --
    
    def __setitem__(self, key, val):
        if not isinstance(val, self._resource_types):
            raise Error("gws.model.ResourceSet", "__setitem__", f"The value must be an instance of {self._resource_types}. The actual value is a {type(val)}.")
        
        self.set[key] = val

    def save(self, *args, **kwrags):
        with DbManager.db.atomic() as transaction:
            try:
                self.data["set"] = {}
                for k in self._set:
                    if not (self._set[k].is_saved() or self._set[k].save()):
                        raise Error("gws.model.ResourceSet", "save", f"Cannot save the resource '{k}' of the resource set")

                    self.data["set"][k] = {
                        "uri": self._set[k].uri,
                        "type": self._set[k].full_classname()
                    }    

                return super().save(*args, **kwrags)

            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.ResourceSet", "save", f"Error: {err}")

    @property
    def set(self):
        from .service.model_service import ModelService
        
        if self.is_saved() and len(self._set) == 0:
            for k in self.data["set"]:
                uri = self.data["set"][k]["uri"]
                rtype = self.data["set"][k]["type"]
                self._set[k] = ModelService.fetch_model(rtype, uri)
        
        return self._set
    
    # -- V --
    
    def values(self):
        return self.set.values()
    
# ####################################################################
#
# ViewModel class
#
# ####################################################################

class ViewModel(Model):
    """ 
    ViewModel class. A view model is parametrized representation of the orginal data

    :property model_id: Id of the Model of the ViewModel
    :type model: int
    :property model_type: Type of the Model of the ViewModel
    :type model_type: str
    :property template: The view template
    :property model_specs: List containing the type of the default Models associated with the ViewModel.
    :type model_specs: list
    """

    model_id: str = IntegerField(index=True) #-> refrence to the model
    model_type: str = CharField(index=True)
    param_hash: str = CharField(index=True)
    model_specs: list = []
        
    _model = None
    _is_transient = False    # transient view are use to temprarily view part of a model (e.g. stream view)
    _table_name = 'gws_view_model'
    _fts_fields = {'title': 2.0, 'description': 1.0}

    def __init__(self, *args, model: Model = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if isinstance(model, Model):
            self._model = model

        if not self.id is None:
            self._model = self.model
        
        if not "params" in self.data or self.data["params"] is None:
            self.data["params"] = {}
        
    # -- A --

    # -- C --
    
    @staticmethod
    def __compute_param_hash(params):
        params = sort_dict_by_key(params)
        h = hashlib.md5()
        h.update( json.dumps(params).encode() )
        return h.hexdigest()
    
    # -- D --
    
    @property
    def description(self) -> str:
        """
        Returns the description. Alias of :meth:`get_description`
        
        :return: The description
        :rtype: str
        """
        
        return self.get_description()

    # -- F --

    # -- G --
    
    def get_instance( model: Model, params: dict ) -> 'ViewModel':
        """
        Retrieve for the db the view model corresponding to a model and a parameter configuration
        
        :param model: The model
        :type model: `gws.model.Model`
        :param params: The parameter dictionnary
        :type params: `dict`
        :return: The retrieved ViewModel
        :rtype: `gws.model.ViewModel`
        """
        
        try:
            h = self.__compute_param_hash(params)
            vm = ViewModel.get( 
                (ViewModel.mode_id==model.id) & 
                (ViewModel.mode_type==model.type) & 
                (ViewModel.param_hash==h) 
            )
        except:
            vm = ViewModel(model=model)
            vm.set_params(params)
            
        return vm
    
    def get_param(self, key: str, default=None) -> str:
        """
        Get a parameter using its key
        
        :param key: The key of the parameter
        :type key: `str`
        :param default: The default value to return if the key does not exist. Defaults to `None`.
        :type default: `str`
        :return: The value of the parameter
        :rtype: `str`
        """
        
        return self.data["params"].get(key, default)
    
    def get_description(self) -> str:
        """
        Returns the description
        
        :return: The description
        :rtype: `str`
        """
        
        return self.data.get("description", "")
    
    def get_title(self) -> str:
        """ 
        Get the title.
        
        :return: The title
        :rtype: `str`
        """
        
        return self.data.get("title", "")
    
    # -- H --
    
    
            
    # -- M --

    @property
    def model(self) -> Model:
        """ 
        Get the Model of the ViewModel.
        
        :return: The model instance
        :rtype: `gws.model.Moldel`
        """
        
        from .service.model_service import ModelService
        
        if not self._model is None:
            return self._model

        model_t = v.get_model_type(self.model_type)
        model = model_t.get(model_t.id == self.model_id)
        self._model = model.cast()
        return self._model
    
    # -- P -- 
    
    @property
    def params(self) -> dict:
        """ 
        Get the parameter set
        
        :return: The parameter set
        :rtype: `dict`
        """
        
        return self.data["params"]
    
    # -- R --

    # -- S --
    
    def set_param(self, key, value):  
        self.data["params"][key] = value
        
    def set_params(self, params: dict={}):  
        if params is None:
            params = {}
        
        if not isinstance(params, dict):
            raise Error("gws.model.ViewModel", "set_params", "Parameter must be a dictionnary")

        self.data["params"] = sort_dict_by_key(params)
        
    def set_description(self, text: str):
        """
        Returns the description.
        
        :param text: The description text
        :type text: `str`
        """
        
        self.data["description"] = text
    
    def set_model(self, model: None):
        if not self.model_id is None:
            raise Error("gws.model.ViewModel", "set_model", "A model already exists")
        
        self._model = model

        if model.is_saved():
            self.model_id = model.id

    def set_title(self, title: str):
        """ 
        Set the title

        :param title: The title
        :type title: str
        """
        self.data["title"] = title
    

    def save(self, *args, **kwargs):
        """
        Saves the view model
        """
        
        if self._is_transient:
            return True
        
        if self._model is None:
            raise Error("gws.model.ViewModel", "save", "The ViewModel has no model")
        else:
            if not self.model_id is None and self._model.id != self.model_id:
                raise Error("gws.model.ViewModel", "save", "It is not allowed to change model of the ViewModel that is already saved")
                
            with DbManager.db.atomic() as transaction:
                try:
                    if self._model.save(*args, **kwargs):
                        self.model_id = self._model.id
                        self.model_type = self._model.full_classname()
                        
                        # hash params
                        params = sort_dict_by_key(self.params)
                        self.set_params(params)
                        self.param_hash = self.__compute_param_hash( params )
                        
                        return super().save(*args, **kwargs)
                    else:
                        raise Error("gws.model.ViewModel", "save", "Cannot save the vmodel. Please ensure that the model of the vmodel is saved before")
                except Exception as err:
                    transaction.rollback()
                    raise Error("gws.model.ViewModel", "save", f"Error message: {err}")
    
    # -- T --
    
    @property
    def title(self):
        """ 
        Get the title.
        """
        
        return self.data.get("title", "")
    
    @title.setter
    def title(self, text:str):
        """ 
        Set the title.
        """
        
        if self.data is None:
            self.data = {}
            
        self.data["title"] = text

    
    def to_json(self, *, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(**kwargs)
        _json["model"] = self.model.to_json( **self.params )
        
        del _json["model_id"]
        del _json["model_type"]
        del _json["param_hash"]
        
        if not self.is_saved():
            _json["uri"] = ""
            _json["save_datetime"] = ""

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    class Meta:
        indexes = (
            # create a unique on model_uri,model_type,param_hash
            (('model_id', 'model_type', 'param_hash'), True),
        )
        
# ####################################################################
#
# StreamViewModel class
#
# ####################################################################

class StreamViewModel(ViewModel):
    _is_transient = True
    
    
    # -- G --
    
    def get_instance( model, params ):
        vm = ViewModel(model=model)
        vm.set_params(params)
        return vm