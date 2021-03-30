# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import asyncio
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
from datetime import datetime

#from base64 import b64encode, b64decode
#from secrets import token_bytes

from datetime import datetime
from peewee import SqliteDatabase, Model as PWModel
from peewee import  Field, IntegerField, FloatField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField, ManyToManyField, IPField, TextField, BlobField, \
                    AutoField, BigAutoField
from playhouse.sqlite_ext import JSONField, SearchField, RowIDField

from gws.logger import Error, Info
#from gws.store import KVStore
from gws.settings import Settings
from gws.base import format_table_name, slugify, BaseModel, BaseFTSModel, DbManager
from gws.controller import Controller
from gws.io import Input, Output, InPort, OutPort, Connector, Interface, Outerface
from gws.event import EventListener
from gws.utils import to_camel_case, sort_dict_by_key, generate_random_chars
from gws.http import *

# ####################################################################
#
# Model class
#
# ####################################################################
 
class Model(BaseModel):
    """
    Model class

    :property id: The id of the model (in database)
    :type id: int, `peewee.model.IntegerField`
    :property uri: The Unique Resource Identifier of the model
    :type uri: str, `peewee.model.CharField`
    :property type: The type of the model (the full Python class name)
    :type type: str, `peewee.model.CharField`
    :property creation_datetime: The creation datetime of the model (on the server)
    :type creation_datetime: datetime, `peewee.model.DateTimeField`
    :property save_datetime: The last save datetime in database
    :type save_datetime: datetime, `peewee.model.DateTimeField`
    :property data: The data of the model
    :type data: dict, `peewee.model.JSONField`
    """
    
    id = IntegerField(primary_key=True)
    uri = CharField(null=True, index=True)
    type = CharField(null=True, index=True)
    creation_datetime = DateTimeField(default=datetime.now)
    save_datetime = DateTimeField()  
    data = JSONField(null=True)
    is_archived = BooleanField(default=False, index=True)
    is_deleted = BooleanField(default=False, index=True)

    _kv_store: 'KVStore' = None

    _is_singleton = False
    _is_deletable = True
    _fts_fields = {}

    _table_name = 'gws_model'
    
    __lab_uri = ""
    
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
            #if not Model.__lab_uri:
            #    Model.__lab_uri = Settings.retrieve().get_data("uri", default="")
            #self.uri = Model.__lab_uri + "-" + str(uuid.uuid4())
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
        if self.is_archived == tf:
            return True
            
        self.is_archived = tf
        return self.save()
    
    def as_json(self, stringify: bool=False, prettify: bool=False, jsonifiable_data_keys: list=[], **kwargs) -> (str, dict, ):
        """
        Returns a JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :param jsonifiable_data_keys: If is empty, `data` is fully jsonified, otherwise only specified keys are jsonified
        :type jsonifiable_data_keys: `list` of str        
        :return: The representation
        :rtype: dict, str
        """
      
        _json = {}
        
        if not isinstance(jsonifiable_data_keys, list):
            jsonifiable_data_keys = []
            
        exclusion_list = (ForeignKeyField, ManyToManyField, BlobField, AutoField, BigAutoField, )
        
        for prop in self.property_names(Field, exclude=exclusion_list) :
            if prop in ["id"]:
                continue
                
            val = getattr(self, prop)
            
            if prop == "data":
                _json[prop] = {}
                
                if len(jsonifiable_data_keys) == 0:
                    _json[prop] = val
                else:
                    for k in jsonifiable_data_keys:
                        if k in val:
                            _json[prop][k] = val[k]
            else:
                if isinstance(val, (datetime, DateTimeField, DateField)):
                    _json[prop] = str(val)
                else:
                    _json[prop] = val
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    # -- B --
    
    @staticmethod
    def barefy( data: dict ):
        if isinstance(data, dict):
            data = json.dumps(data)
        
        data = re.sub(r"\"(([^\"]*_)?uri|save_datetime|creation_datetime)\"\s*\:\s*\"([^\"]*)\"", r'"\1": ""', data)
        return json.loads(data)
    
    # -- C --

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database

        :return: The model
        :rtype: `Model` instance
        """

        #new_model_t = Controller.get_model_type(self.type)
        #if type(self) == new_model_t:
        #    return self
        
        if self.type == self.full_classname():
            return self
        
        # instanciate the class and shallow copy data
        new_model_t = Controller.get_model_type(self.type)
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
        super.delete_instance(*args, **kwargs)
        
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
        cursor = DbManager.db.execute_sql(f'SELECT type FROM {self._table_name} WHERE id = ?', (str(id),))
        row = cursor.fetchone()
        if len(row) == 0:
            raise Error("gws.model.Model", "fetch_type_by_id", "The model is not found.")
        type_str = row[0]
        model_t = Controller.get_model_type(type_str)
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
        return not self.id is None

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
    
    def remove(self) -> bool:
        if not self._is_deletable:
            return False

        if self.is_deleted:
            return True
 
        self.is_deleted = True
        return self.save()
    
    # -- S --

    @classmethod
    def select(cls):
        if not cls.table_exists():
            cls.create_table()
            
        return super().select()

    @classmethod
    def select_me(cls):
        if not cls.table_exists():
            cls.create_table()

        return cls.select().where(cls.type == cls.full_classname())
    
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
            return False
        
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
                if Settings.retrieve().is_fts_active:
                    if not _FTSModel is None:
                        if not self._save_fts_document():
                            raise Error("gws.model.Model", "save", "Cannot save related FTS document")

                #self.kv_store.save()
                self.save_datetime = datetime.now()
                return super().save(*args, **kwargs)
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Model", "save", f"Error message: {err}")



    @classmethod
    def save_all(cls, model_list: list = None) -> bool:
        """
        Atomically and safely save a list of models in the database. If an error occurs
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

# ####################################################################
#
# User class
#
# ####################################################################

class User(Model):
    
    token = CharField(null=False)
    email = CharField(default=False, index=True)
    group = CharField(default="user", index=True)
    is_active = BooleanField(default=True)
    is_authenticated = BooleanField(default=False)

    USER_GOUP = "user"
    ADMIN_GROUP = "admin"
    OWNER_GROUP = "owner"
    SYSUSER_GROUP = "sysuser"
    VALID_GROUPS = [USER_GOUP, ADMIN_GROUP, OWNER_GROUP, SYSUSER_GROUP]
    
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
                if not user.is_active:
                    raise Error("User", "authenticate", f"Could not authenticate inactive user {uri}")
                    
                user.is_authenticated = True
                user.save()
                Activity.add(user, Activity.LOGIN)
                return user
            except:
                transaction.rollback()
                return False
    
    @classmethod
    def create_owner_and_sysuser(cls):
        settings = Settings.retrieve()

        Q = User.select().where(User.group == cls.OWNER_GROUP)
        if not Q:
            uri = settings.data["owner"]["uri"]
            email = settings.data["owner"]["email"]
            full_name = settings.data["owner"]["full_name"]
            u = User(
                uri = uri if uri else None, 
                email = email,
                data = {"full_name": full_name},
                is_active = True,
                group = cls.OWNER_GROUP
            )
            u.save()
            
        Q = User.select().where(User.group == cls.SYSUSER_GROUP)
        if not Q:
            u = User(
                email = "sys@local",
                data = {"full_name": "sysuser"},
                is_active = True,
                is_authenticated = True,   #<- is always authenticated
                group = cls.SYSUSER_GROUP
            )
            u.save()
            
    # -- G --
    
    @classmethod
    def get_owner(cls):
         return User.get(User.group == cls.OWNER_GROUP)
    
    @classmethod
    def get_sysuser(cls):
         return User.get(User.group == cls.SYSUSER_GROUP)
    
    @property
    def full_name(self):
        return self.data.get("full_name", "")

    def __generate_token(self):
        return generate_random_chars(128)
    
    def generate_access_token(self):
        self.token =  self.__generate_token()
        self.save()
    
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
    
    # -- S --

    def save(self, *arg, **kwargs):
        if not self.group in self.VALID_GROUPS:
            raise Error("User", "save", "Invalid user group")
        
        if self.id is None:
            if self.token is None:
                self.token = self.__generate_token()
        
        if self.is_owner or self.is_admin or self.is_sysuser:
            if not self.is_active:
                raise Error("User", "save", "Cannot deactivate the {owner, admin, system} users")
                
        return super().save(*arg, **kwargs)
    
    # -- U --
    
    @classmethod
    def unauthenticate(self, uri: str) -> 'User':
        with DbManager.db.atomic() as transaction:
            try:
                user = User.get(User.uri==uri, User.token==token)
                self.is_authenticated = False
                self.token = self.__generate_token()     #/!\SECURITRY: cancel current token to prevent token hacking
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
    user = ForeignKeyField(User, index=True)
    activity_type = CharField(null=False, index=True)
    object_type = CharField(null=False, index=True)
    object_uri = CharField(null=False, index=True)
    
    _is_deletable = False
    
    _fts_fields = {}
    _table_name = "gws_user_activity"
    
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    SAVE = "SAVE"
    START = "START"
    STOP = "STOP"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    VALIDATE = "VALIDATE"
    
    @classmethod
    def add(self, user: User, activity_type: str, object_type=None, object_uri=None):
        activity = Activity(
            user = user, 
            activity_type = activity_type,
            object_type = object_type,
            object_uri = object_uri
        )
        activity.save()
        
# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):

    _fts_field = {'title': 2.0, 'description': 1.0}

    # -- A --

    def archive(self, tf: bool):
        if self.is_archived == tf:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                Q = ViewModel.select().where( ViewModel.model_id == self.id )
                for vm in Q:
                    if not vm.archive(tf):
                        transaction.rollback()
                        return False
                
                if super().archive(tf):
                    return True
                else:
                    transaction.rollback()
                    return False
            except:
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

    def remove(self):
        if self.is_deleted:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                Q = ViewModel.select().where( ViewModel.model_id == self.id )
                for vm in Q:
                    if not vm.remove():
                        transaction.rollback()
                        return False
                
                if super().remove():
                    return True
                else:
                    transaction.rollback()
                    return False
            except:
                transaction.rollback()
                return False

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

    def view(self, *args, format="json", params:dict = {}) -> dict:
        if not isinstance(params, dict):
            params = {}

        view_model = ViewModel.get_instance(self, params)
        return view_model
                
    
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

    def archive(self, tf: bool):
        if self.is_archived == tf:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.config_uri == self.uri )
                for job in Q:
                    if not job.archive(tf):
                        transaction.rollback()
                        return False
                
                if super().archive(tf):
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except:
                transaction.rollback()
                return False

    # -- D --

    def remove(self):
        if self.is_deleted:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.config_uri == self.uri )
                for job in Q:
                    if not job.remove():
                        transaction.rollback()
                        return False
                
                if super().remove():
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except:
                transaction.rollback()
                return False

    # -- G --

    def get_param(self, name: str) -> [str, int, float, bool]:
        """ 
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: [str, int, float, bool]
        """
        if not name in self.specs:
            raise Error("gws.model.Config", "get_param", f"Parameter {name} does not exist'")
        
        default = self.specs[name].get("default", None)
        return self.data["params"].get(name,default)

    # -- P --

    @property
    def params(self) -> dict:
        """ 
        Returns specs
        """
        return self.data["params"]

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

# ####################################################################
#
# Process class
#
# ####################################################################

class Process(Viewable):
    """
    Process class.
    
    :property is_running: State of the process, True if the process is running, False otherwise
    :type is_running: bool
    :property is_finished: State of the process, True if the process has finished to run, Flase otherwise
    :type is_finished: bool
    :property input_specs: The specs of the input
    :type input_specs: dict
    :property output_specs: The specs of the output
    :type output_specs: dict
    :property config_specs: The specs of the config
    :type config_specs: dict
    """

    type = CharField(null=True, index=True, unique=True)
    created_by = ForeignKeyField(User, null=False, index=True)
    
    is_running: bool = False 
    is_finished: bool = False 
    
    input_specs: dict = {}
    output_specs: dict = {}
    config_specs: dict = {}
    
    _file_store: 'FileStore' = None
    _parent_protocol: 'Protocol' = None
    _instance_name: str = None
    _event_listener: EventListener = None
    _input: Input = None
    _output: Output = None
    _job: 'Job' = None  #ref to the current job

    _is_singleton = True
    _is_deletable = False
    _table_name = 'gws_process'

    def __init__(self, *args, instance_name: str=None, user=None, **kwargs):
        """
        Constructor

        :property instance_name: The canonical name of the process instance (in the context of the protocol it belongs to). 
        It is related to the current in-memory instance. It is therefore not saved in db.
        :type instance_name: `str`        
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

        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        self._event_listener = EventListener()

        if not self.title:
            self.data["title"] = kwargs.get('title', self.full_classname())
        
        if not self.title:
            self.data["title"] = kwargs.get('title', self.full_classname())
            
        if not self.is_saved():
            if not user:
                user = User.get_sysuser()            
            
            if not isinstance(user, User):
                raise Error("gws.model.Process", "__init__", "The user must be an instance of User")
                
            self.created_by = user

        self.set_instance_name(instance_name)
        self.save()

    # -- A --

    def add_event(self, name, callback: callable):
        """
        Adds an event the event listener

        :param name: The name of the event
        :type name: `str`
        :param callback: The callback function of the event
        :type callback: `function`
        """
        try:
            self._event_listener.add( name, callback )
        except Exception as err:
            raise Error("gws.model.Process", "add_event", f"Cannot add event. Error message: {err}")
    
    def as_json(self, bare: bool=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().as_json(**kwargs)
        _json["input_specs"] = self.input.as_json()
        _json["output_specs"] = self.output.as_json()
        _json["config_specs"] = self.config_specs
        
        if bare:
            _json["uri"] = ""
            _json["save_datetime"] = ""
            _json["creation_datetime"] = ""
        
        for k in _json["config_specs"]:
            spec = _json["config_specs"][k]
            if "type" in spec and isinstance(spec["type"], type):
                t_str = spec["type"].__name__ 
                _json["config_specs"][k]["type"] = t_str
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
    
    # -- B --
    
    @staticmethod
    def barefy( data: dict ):
        if isinstance(data, dict):
            data = json.dumps(data)
        
        data = re.sub(r"\"(([^\"]*_)?uri|save_datetime|creation_datetime)\"\s*\:\s*\"([^\"]*)\"", r'"\1": ""', data)
        return json.loads(data)
    
    # -- C --
    
    def create_experiment(self, user: 'User', study: 'Study'):
        """
        Create an experiment using a protocol composed of this process
        
        :param study: The study in which the experiment is realized
        :type study: `gws.model.Study`
        :param study: The configuration of protocol
        :type study: `gws.model.Config`
        :return: The experiment
        :rtype: `gws.model.Experiment`
        """
        
        instance_name = self.instance_name if self.instance_name else self.full_classname()
        proto = Protocol(processes={ instance_name: self })
        e = Experiment(user=user, study=study, protocol=proto)
        e.save()
        return e
    
    @classmethod
    def create_table(cls, *args, **kwargs):
        if not Job.table_exists():
            Job.create_table()
        
        if not Config.table_exists():
            Config.create_table()

        super().create_table(*args, **kwargs)

    @property
    def config(self) -> Config:
        """
        Returns the config. 
        
        Note that the config is actually related to the job of the process. 
        The config is therefore retrieved 
        through the job instance.

        :return: The config
        :rtype: Config
        """
        
        return self.job.config

    def create_source_zip(self):
        model_t = Controller.get_model_type(self.type) #/:\ Use the true object type (self.type)
        source = inspect.getsource(model_t)
        return zlib.compress(source.encode())
    
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
    def instance_name(self):
        """
        The instance name of the process in the context of a protocol

        :return: The instance name
        :rtype: `str`
        """
        return self._instance_name
    
    @property
    def input(self) -> 'Input':
        """
        Returns input of the process.

        :return: The input
        :rtype: Input
        """
        return self._input


    @property
    def is_ready(self) -> bool:
        """
        Returns True if the process is ready (i.e. all its ports are 
        ready or it has never been run before), False otherwise.

        :return: True if the process is ready, False otherwise.
        :rtype: bool
        """
        return (not self.is_running and not self.is_finished) and self._input.is_ready 

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
    
    @property
    def job(self):
        """
        Initialize an job for the process.

        :return: The job
        :rtype: Job
        """

        if self._job is None:
            config = Config(specs = self.config_specs)
            self._job = Job(process=self, config=config)

        return self._job
    
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

    def on_end(self, callback: callable):
        """
        Adds an event to execute after the process ends running. 

        :param callback: The function to execute
        :callback: `function`
        """
        self.add_event('end', callback)

    def on_start(self, callback: callable):
        """
        Adds an event to execute before the process starts running. 

        :param callback: The function to execute
        :callback: `function`
        """
        self.add_event('start', callback)
    
    # -- P --

    # -- R -- 
    
    async def _run(self):
        """ 
        Runs the process and save its state in the database.
        """
        
        if not self.is_ready:
            return
        
        await self._run_before_task()
        await self.task()
        await self._run_after_task()
    
    async def _run_next_processes(self):
        self._output.propagate()
        aws  = []
        job = self.job
        for proc in self._output.get_next_procs():
            # ensure that the next process is held by this experiment
            #proc_job = proc.job
            #proc_job.experiment = job.experiment
            #proc_job.save()

            # run next
            aws.append( proc._run() )
            #await proc._run() 

        if len(aws):
            await asyncio.gather( *aws )
                
    async def _run_before_task( self, *args, **kwargs ):

        self.is_running = True
        
        if self.get_title():
            Info(f"Running {self.full_classname()} '{self.get_title()}' ...")
        else:
            Info(f"Running {self.full_classname()} ...")
        
        job = self.job
        if not job.progress_bar.is_started:
            job.progress_bar.start()
            
        if not job.save():
            raise Error("gws.model.Process", "_run_before_task", "Cannot save the job")
        
        if self._event_listener.exists('start'):
            self._event_listener.sync_call('start', self)
            await self._event_listener.async_call('start', self)

    async def _run_after_task( self, *args, **kwargs ):
        if self.get_title():
            Info(f"Task of {self.full_classname()} '{self.get_title()}' successfully finished!")
        else:
            Info(f"Task of {self.full_classname()} successfully finished!")

        self.is_running = False
        self.is_finished = True

        job = self.job
        job.progress_bar.stop()
        if not job.save():
            raise Error("gws.model.Process", "_run_after_task", f"Cannot save the job")

        res = self.output.get_resources()
        for k in res:
            if not res[k] is None:
                res[k]._set_job(job)
                res[k].save()
        
        if not self._output.is_ready:
            return
        
        if self._event_listener.exists('end'):
            self._event_listener.sync_call('end', self)
            await self._event_listener.async_call('end', self)
        
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
    
    def set_instance_name(self, name:str = None ):
        default_name = self.full_classname()
        if name is None:
            name = default_name
        
        if self._instance_name:
            if self._instance_name.startswith(default_name):
                self._instance_name = name
        else:            
            self._instance_name = name
        
        if self._instance_name != name:
            raise Error("gws.model.Process", "set_instance_name", "Try to set a different instance name")
            
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

        if isinstance(config, Config):
            job = self.job
            job.set_config(config)
        else:
            raise Error("gws.model.Process", "set_config", "The config must be an instance of Config.")

    def set_param(self, name: str, value: [str, int, float, bool]):
        """ 
        Sets the value of a config parameter.

        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """
        
        self.config.set_param(name, value)

    # -- T --

    async def task(self):
        pass


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

    :property protocol_job: The job of the protocol of the experiment
    :type job: Job
    :property protocol_uri: The uri of the protocol of the experiment
    :type protocol_uri: str
    :property score: The score of the experiment
    :type score: `float`
    """

    study = ForeignKeyField(Study, null=True, backref='experiments')
    created_by = ForeignKeyField(User, null=True, backref='created_experiments')
    score = FloatField(null=True, index=True)    
    is_validated = BooleanField(default=False, index=True)

    _job = None
    _protocol = None
    _table_name = 'gws_experiment'

    def __init__(self, *args, user=None, protocol=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.is_saved():
            if user is None:
                user = User.get_sysuser()
            
            if isinstance(user, User):
                self.created_by = user
            else:
                raise Error("gws.model.Experiment", "__init__", "The user must be an instance of User")
                
            if protocol is None:
                protocol = Protocol(user=user)
                
            if isinstance(protocol, Protocol):
                if not protocol.instance_name:
                    protocol.set_instance_name()
            else:
                raise Error("gws.model.Experiment", "__init__", "The protocol must be an instance of Protocol")
                
            self.save()
            
            # bind a job
            protocol.save()
            self._job = protocol.job
            self._job.set_experiment(self)        
        
    # -- A --
    
    def add_report(self, report: 'Report'):
        report.experiment = self

    def archive(self, tf:bool):
        if self.is_archived == tf:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Activity.add(
                    user, 
                    Activity.ARCHIVE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )
                
                Q = Job.select().where( Job.experiment == self )
                for job in Q:
                    if not job.archive(tf):
                        transaction.rollback()
                        return False
                
                if super().archive(tf):
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except:
                transaction.rollback()
                return False

    def as_json(self, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().as_json(**kwargs)
        _json.update({
            "is_running": self.is_running,
            "is_finished": self.is_finished,
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
      
    # -- C --
  
    # -- F --
    
    @property
    def flow(self):
        return self.job.flow
    
    @classmethod
    def from_flow(cls, flow: dict, user=None) -> 'Experiment':
        """ 
        Create a new instance from a existing frow

        :return: The experiment
        :rtype": `gws.model.Experiment`
        """
        
        if not user:
            user = User.get_sysuser()
            
        if isinstance(flow, str):
            flow = json.loads(flow)
        
        if len(flow) == 0:
            return None
        
        if flow.get("experiment_uri"):
            e_uri = flow["experiment_uri"]
            try:
                e = Experiment.get(Experiment.uri == e_uri)
            except:
                raise Error("Experiment", "Experiment", f"No experiment matchs against the uri {e_uri}")
        else:
            if not flow.get("study_uri"):
                raise Error("Experiment", "Experiment", "A study uri is required")
            
            try:
                study = Study.get(Study.uri == flow.get("study_uri"))
            except:
                raise Error("Experiment", "Experiment", f"No study matchs against the uri {study_uri}")
      
            protocol = Protocol.from_flow(flow, user=user)
            protocol.save()
            
            e = protocol.create_experiment(study=study, user=user)
            e.save()

        return e
        
        
    # -- I --
    
    @property
    def is_draft(self):
        return not self.is_running and not self.is_finished
    
    @property
    def is_finished(self):
        for job in self.jobs:
            if not job.is_finished:
                return False

        return True

    @property
    def is_running(self):
        for job in self.jobs:
            if not job.is_running:
                return True

        return False
    
    # -- J --
    
    @property
    def job(self):
        if not self._job:
            self._job = Job.get(Job.experiment == self)
        
        return self._job
    
    # -- O --

    def on_end(self, call_back: callable):
        self.protocol.on_end(call_back)
         
    def on_start(self, call_back: callable):
        self.protocol.on_start(call_back)
        
    # -- P --
    
    @property 
    def protocol(self):
        return self.job.process
     
    # -- R --
    
    def remove(self):
        if self.is_deleted:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.experiment == self )
                for job in Q:
                    if not job.remove():
                        transaction.rollback()
                        return False
                
                if super().remove():
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except:
                transaction.rollback()
                return False
            
    @property 
    def resources(self):
        Q = Resource.select() \
                    .join(Job) \
                    .join(Experiment) \
                    .where(Experiment.uri == self.uri) \
                    .order_by(Resource.creation_datetime.desc())
        return Q

    async def run(self, user=None):
        if not user:
            user = User.get_sysuser()
            
        if self.is_deleted:
            raise Error("gws.model.Experiment", "save", f"The experiment is deleted")
        
        if self.is_archived:
            raise Error("gws.model.Experiment", "save", f"The experiment is archived")
        
        if self.is_validated:
            raise Error("gws.model.Experiment", "save", f"The experiment is validated")
        
        Activity.add(
            user, 
            Activity.START,
            object_type = self.full_classname(),
            object_uri = self.uri
        )
        
        self.save()
        await self.protocol._run()
    
    # -- S --
    
    def save(self, *args, **kwargs):  
        with DbManager.db.atomic() as transaction:
            try:
                if not self.is_saved():
                    Activity.add(
                        self.created_by,
                        Activity.CREATE,
                        object_type = self.full_classname(),
                        object_uri = self.uri
                    )
                
                return super().save(*args, **kwargs)
            except:
                transaction.rollback()
                return False
    
    # -- V --
    
    def validate(self, user):
        if self.is_validated:
            raise Error("gws.model.Experiment", "save", f"The experiment is already validated")
        
        with DbManager.db.atomic() as transaction:
            try:
                self.is_validated = True
                self.save()
                
                Activity.add(
                    user,
                    Activity.VALIDATE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )
            except:
                transaction.rollback()
                raise Error("gws.model.Experiment", "save", f"Could not validate the experiment. Error: {err}")
            
# ####################################################################
#
# ProgressBar class
#
# ####################################################################

class ProgressBar(Model):
    _min_allowed_delta_time = 1.0
    _min_value = 0.0
    
    _is_deletable = False
    _table_name = "gws_job_progress_bar"
    
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
            }
            self.save()
        
    @property
    def is_started(self):
        return self.data["start_time"] > 0.0
    
    @property
    def is_stopped(self):
        return self.data["value"] >= self.data["max_value"]
    
    def start(self, max_value: float = 100.0):
        if max_value <= 0.0:
            raise Error("ProgressBar", "start", "Invalid max value")
    
        if self.data["start_time"] > 0.0:
            raise Error("ProgressBar", "start", "The progress bar has already started")
        
        self.data["max_value"] = max_value
        self.data["start_time"] = time.perf_counter()
        self.save()
    
    def stop(self):
        _max = self.data["max_value"]
        
        if self.data["value"] < _max:
            self.change(_max)

        self.data["remaining_time"] = 0.0
        self.save()
        
    def change(self, value: float):
        """Increment the progress-bar value"""
        
        _max = self.data["max_value"]        
        if _max == 0.0:
            raise Error("ProgressBar", "start", "The progress bar has not started")
            
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
        
        if self.data["value"] == _max:
            self.stop()
        else:
            self.save()
        
    def _compute_remaining_seconds(self):
        nb_remaining_steps = self.data["max_value"] - self.data["value"]
        nb_remaining_seconds = nb_remaining_steps / self.data["average_speed"]
        return nb_remaining_seconds
    
# ####################################################################
#
# Job class
#
# ####################################################################

class Job(Viewable):
    """
    Job class.
    
    :property parent_job: The parent job (i.e. the job of the parent protocol)
    :type parent_job: Job
    :property process_uri: The uri of the job's process
    :type process_uri: str
    :property process_type: The type if the job's process
    :type process_type: str
    :property process_source: The source code of the job's process
    :type process_source: binary
    :property config_uri: The uri of config of the job's process
    :type config_uri: str
    :property experiment: The experiment of the job
    :type experiment: Experiment
    :property progress: The progress of the experiment. Between 0 (not started) and 100 (fininshed).
    :type progress: integer 
    """
    
    parent_job = ForeignKeyField('self', null=True, backref='children')
    process_uri = CharField(null=False, index=True)                         # save uri it may represent different type of process
    process_type = CharField(null=False) 
    process_source = BlobField(null=True)                  
    config_uri = CharField(null=False, index=True)                          # save uri as it may represent different config classes
    experiment = ForeignKeyField(Experiment, null=True, backref='jobs')     # only valid for protocol
    progress_bar = ForeignKeyField(ProgressBar, null=True, backref='job')
    
    _process: Process = None
    _config: Config = None
    _table_name = 'gws_job'
    _fts_fields = {}
    
    def __init__(self, *args, process: Process = None, config: Config = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.id:
            if (not config is None) and (not isinstance(config, Config)):
                raise Error("gws.model.Job", "__init__", "The config must be an instance of Config")
 
            if (not process is None) and (not isinstance(process, Process)):
                raise Error("gws.model.Job", "__init__", "The process must be an instance of Process")
            
            self._config = config            
            self._process = process
            
            #if not process.instance_name:
            #    raise Error("gws.model.Job", "__init__", "The process has no instance name.")
            
            self.progress_bar = ProgressBar()
            self.data["instance_name"] = process.instance_name
            
            self.save()
        
        # set active process job
        self.process._job = self
     
    # -- A --

    def archive(self, tf: bool):
        # /!\ Do not archive Config, Process and Experiment
        if self.is_archived == tf:
            return True

        return super().archive(tf)
    
    @property
    def instance_name(self) -> str:
        """
        Returns the instance name of the job (i.e. of the process) in the context of the current protocol.

        :return: The instance name
        :rtype: `str`
        """
        
        return self.data["instance_name"]
    
    def as_json(self, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().as_json(**kwargs)

        if not self.parent_job is None:
            parent_job_uri = self.parent_job.uri
        else:
            parent_job_uri = None
        
        if "data" in _json:
            del _json["data"]
        
        config_specs = self.process.config_specs
        for k in config_specs:
            spec = config_specs[k]
            if isinstance(spec.get("type",None), type):
                config_specs[k]["type"] = spec["type"].__name__ 
        
        _json.update({
            "process": {
                "uri": self.process.uri,
                "type": self.process.type,
                "title": self.process.title,
                "instance_name": self.instance_name, #do not use self.process.instance_name as it is not saved on db
                "config_specs": config_specs,
                "input_specs": self.process.input.as_json(),
                "output_specs": self.process.output.as_json()
            },
            "config": {
                "uri": self.config.uri,
                "type": self.config.type,
                "params": self.config.params,
            },
            "study_uri": self.experiment.study.uri,
            "experiment_uri": self.experiment.uri,
            "progress_bar": self.progress_bar.as_json(),
            "parent_job_uri": parent_job_uri,
            "is_running": self.is_running,
            "is_finished": self.is_finished
        })
        
        if isinstance(self.process, Protocol):
            inter = {}
            outer = {}
            for k in self.process._interfaces:
                inter[k] = self.process._interfaces[k].as_json()

            for k in self.process._outerfaces:
                outer[k] = self.process._outerfaces[k].as_json()
            
            _json["layout"] = self.process.get_layout()
            _json["process"].update({
                "interfaces" : inter,
                "outerfaces" : outer
            })
                
        # clean redundant information
        del _json["process_type"]
        del _json["process_uri"]
        del _json["config_uri"]
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- C --
    
    @property
    def created_by(self):
        return self.experiment.created_by
    
    @property
    def config(self):
        """
        Returns the config fo the job.

        :return: The config
        :rtype: Config
        """

        if self._config:
            return self._config

        if self.config_uri:
            config = Config.get(Config.uri == self.config_uri)
            self._config = config.cast()
            return self._config
        else:
            return None

    # -- F -- 
    
    @property
    def flow(self):
        if not self.is_finished:
            return {}
        
        if not len(self.children):
            return {}
        
        protocol = self.process
        
        if not isinstance(protocol, Protocol):
            raise Error("gws.model.Job", "flow", "The job must be related ot a protocol")     
        
        flow = self.as_json()
    
        if "data" in flow:
            del flow["data"]
            
        flow.update({
            "jobs": {},
            "flows": []
        })
    
        flow["layout"] = protocol.get_layout()
    
        for job in self.children:
            instance_name = job.instance_name
            flow["jobs"][instance_name] = job.as_json()

            for k in job.data["input"]:
                _input = job.data["input"][k]
                flow["flows"].append({
                    "from": _input["previous"],
                    "to": {
                        "job_uri": job.uri,
                        "process": {
                            "uri": job.process.uri,
                            "instance_name": job.process.instance_name,
                            "port": k,
                        }
                    },
                    "resource_uri": _input["resource_uri"]
                })

        return flow
    
    
    # -- G --

        
    # -- I --
    
    @property
    def is_running(self):
        return self.progress_bar.is_started
    

    @property
    def is_finished(self):
        return self.progress_bar.is_stopped
    
    # -- P --
    
    def _propagate_experiment(self, experiment):
        if isinstance(self.process, Protocol):
            proto = self.process
            for k in proto._processes:
                subjob = proto._processes[k].job
                subjob.set_experiment(experiment)
            
    @property
    def process(self):
        """
        Returns the process fo the job.

        :return: The config
        :rtype: Config
        """

        if self._process:
            return self._process

        if self.process_uri:
            process_t = Controller.get_model_type(self.process_type)
            proc = process_t.get(process_t.uri == self.process_uri)
            self._process = proc.cast()
            self._process.set_instance_name(self.instance_name)
            return self._process
        else:
            return None

    # -- R --
    
    def remove(self):
        # /!\ Do not archive Config, Process nor Experiment
        if self.is_deleted:
            return True

        return super().remove()
    
    async def _run( self ):
        await self.process._run()

    # -- S --
    
    @property
    def study(self):
        return self.experiment.study
    
    def set_config(self, config: Config):
        if not config.is_saved():
            config.save()
            self.config_uri = config.uri
        self._config = config
        
    def set_experiment(self, experiment: 'Experiment'):
        if not isinstance(experiment, Experiment):
            raise Error("gws.model.Job", "set_experiment", "The experiment must be an instance of Experiment")
        
        if self.experiment == experiment:
            return
        
        if self.experiment is None:
            self.experiment = experiment
        else:
            raise Error("gws.model.Job", "set_experiment", "An experiment is already defined") 
        
        self.save()
        
        self._propagate_experiment(experiment)
        
    def save(self, *args, **kwargs):
        """ 
        Save the job 
        """
        
        with DbManager.db.atomic() as transaction:
            try:
                if self.process is None:
                    raise Error("gws.model.Job", "save", "Cannot save the job. The process is not saved.")

                if not self.config.save():
                    raise Error("gws.model.Job", "save", "Cannot save the job. The config cannnot be saved.")
                
                if not self.progress_bar.save():
                    raise Error("gws.model.Job", "save", "Cannot save the job. The progress_bar cannnot be saved.")

                self.process_uri = self._process.uri
                self.process_type = self._process.type
                self.process_source = self._process.create_source_zip()
                self.config_uri = self._config.uri

                if not self._process._parent_protocol is None:
                    self.parent_job = self._process._parent_protocol.job

                res = self.process.output.get_resources()
                for k in res:
                    if res[k] is None:
                        continue

                    if not res[k].is_saved():
                        if not res[k].save(*args, **kwargs):
                            raise Error("gws.model.Job", "save", f"Cannot save the resource output '{k}' of the job")

                self.__track_input_uri()
                #self.__track_ouput_uri()

                if not super().save(*args, **kwargs):
                    raise Error("gws.model.Job", "save", "Cannot save the job.")

                return True
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Job", "save", f"An error occured. Error: {err}")

    # -- T --
     
    def __track_input_uri(self):
        _input = self.process.input
        self.data["input"] = {}
        for k in _input.ports:
            port = _input.ports[k]
            res = port.resource
            
            is_interfaced = not port.is_left_connected
            
            if res is None:
                self.data["input"][k] = {
                    "resource_uri": "",
                }
            else:
                if not res.is_saved():
                    raise Error("gws.model.Process", "__track_input_uris", f"Cannot track input '{k}' uri. Please save the input resource before.")
                    
                self.data["input"][k] = {
                    "resource_uri": res.uri,
                }

            if not is_interfaced:
                left_port_name = port.prev.name
                prev_proc = port.prev.process
                
                self.data["input"][k].update({
                    "previous": {
                        "job_uri": prev_proc.job.uri,
                        "process": {
                            "uri": prev_proc.uri,
                            "instance_name": prev_proc.instance_name,
                            "port": left_port_name
                        }
                    }
                })
        
    def __track_ouput_uri(self):
        _output = self.process.output
        self.data["output"] = {}
        for k in _output.ports:
            port = _output.ports[k]
            res = port.resource

            if res is None:
                self.data["output"][k] = {
                    "resource_uri": ""
                }
            else:
                if not res.is_saved():
                    raise Error("gws.model.Process", "__track_ouput_uri", f"Cannot track output '{k}' uri. Please save the output resource before.")

                self.data["output"][k] = {
                    "resource_uri": res.uri
                }
        
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

    type = CharField(null=True, index=True, unique=False)
    is_validated = BooleanField(default=False, index=True)
    
    _is_singleton = False
    _processes: dict = {}
    _connectors: list = []
    _interfaces: dict = {}
    _outerfaces: dict = {}
    _defaultPosition: list = [0.0, 0.0]
    
    _table_name = 'gws_protocol'

    def __init__(self, *args, processes: dict = {}, \
                 connectors: list = [], interfaces: dict = {}, outerfaces: dict = {}, \
                 user = None, **kwargs):

        super().__init__(*args, **kwargs, user = None)

        self._processes = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}
        self._defaultPosition = [0.0, 0.0]
        
        if self.uri and self.data.get("graph"):          #the protocol was saved in the super-class
            self.__build_from_dump( self.data["graph"], title=self.title )
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
             
            if user:
                if self.created_by.is_sysuser:
                    self.create_by = user
                
            # set interfaces
            self.__set_interfaces(interfaces)
            self.__set_outerfaces(outerfaces)
            
            self.data["graph"] = self.dumps(as_dict=True)
            self.save()   #<- will save the graph
            
        #self.__init_pre_start_event()
        self.__init_on_end_event()
            

    # -- A --

    def add_process(self, name: str, process: Process):
        """ 
        Adds a process to the protocol.

        :param name: Unique name of the process
        :type name: str
        :param process: The process
        :type process: Process
        """

        if self.is_finished or self.is_running:
            raise Error("gws.model.Protocol", "add_process", "The protocol has already been run")
       
        if not isinstance(process, Process):
            raise Error("gws.model.Protocol", "add_process", f"The process '{name}' must be an instance of Process")

        if not process._parent_protocol is None:
            raise Error("gws.model.Protocol", "add_process", f"The process instance '{name}' already belongs to another protocol")
        
        if name in self._processes:
            raise Error("gws.model.Protocol", "add_process", f"Process name '{name}' already exists")
        
        if process in self._processes.items():
            raise Error("gws.model.Protocol", "add_process", f"Process '{name}' duplicate")
            
        process._parent_protocol = self
        self._processes[name] = process
        process.set_instance_name(name)

    def add_connector(self, connector: Connector):
        """ 
        Adds a connector to the protocol.

        :param connector: The connector
        :type connector: Connector
        """

        if self.is_finished or self.is_running:
            raise Error("gws.model.Protocol", "add_connector", "The protocol has already been run")
        
        if not isinstance(connector, Connector):
            raise Error("gws.model.Protocol", "add_connector", "The connector must be an instance of Connector")
        
        if  not connector.left_process in self._processes.values() or \
            not connector.right_process in self._processes.values():
            raise Error("gws.model.Protocol", "add_connector", "The connector processes must be belong to the protocol")
        
        if connector in self._connectors:
            raise Error("gws.model.Protocol", "add_connector", "Duplciated connector")

        self._connectors.append(connector)
    
    # -- B --
    
    def __build_from_dump( self, graph: (str, dict), title=None ) -> 'Protocol':
        """ 
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """

        if isinstance(graph, str):
            graph = json.loads(graph)
        
        if len(graph) == 0:
            return None
        
        if not title:
            title = graph.get("title", self.full_classname())

        if not self.title or self.title == self.full_classname():
            self.set_title(title)
        
        # create nodes
        
        for k in graph["nodes"]:
            node_json = graph["nodes"][k]
            node_uri = node_json.get("uri",None)
            node_type_str = node_json["type"]
            
            try:
                process_t = Controller.get_model_type(node_type_str)
                
                if process_t is None:
                    raise Exception(f"Process {node_type_str} is not defined. Please ensure that the corresponding brick is loaded.")
                else:
                    if issubclass(process_t, Protocol):
                        proc = Protocol.from_graph( node_json["data"]["graph"] )
                    else:
                        if node_uri:
                            proc = process_t.get(process_t.uri == node_uri)
                        else:
                            proc = process_t()

                    self.add_process( k, proc )

            except Exception as err:
                raise Error("gws.model.Protocol", "__build_from_dump", f"An error occured. Error: {err}")
        
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
            
    # -- C --

    def create_experiment(self, user: 'User', study: 'Study'):
        """
        Realize a protocol by creating a experiment
        
        :param study: The study in which the protocol is realized
        :type study: `gws.model.Study`
        :param config: The configuration of protocol
        :type config: `gws.model.Config`
        :return: The experiment
        :rtype: `gws.model.Experiment`
        """
        
        if not self.instance_name:
            self.set_instance_name()
        
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
            link = conn.as_json()
            graph['links'].append(link)
        
        for k in self._processes:
            proc = self._processes[k]
            graph["nodes"][k] = proc.as_json(bare=bare)

        for k in self._interfaces:
            graph['interfaces'][k] = self._interfaces[k].as_json()

        for k in self._outerfaces:
            graph['outerfaces'][k] = self._outerfaces[k].as_json()

        graph["layout"] = self.get_layout()
        
        if as_dict:
            return graph
        else:
            if prettify:
                return json.dumps(graph, indent=4)
            else:
                return json.dumps(graph)
    
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
            proto.__build_from_dump(graph)
            proto.data["graph"] = proto.dumps(as_dict=True)
            proto.save()
            
        return proto
    
    @classmethod
    def from_flow( cls, flow: dict, user=None ) -> 'Protocol':
        """ 
        Create a new instance from an existing flow

        :return: The protocol
        :rtype": `gws.model.Protocol`
        """
        
        if not user:
            user = User.get_sysuser()
            
        if isinstance(flow, str):
            flow = json.loads(flow)
        
        if len(flow) == 0:
            return None
         
        if flow["process"].get("uri"):
            proto = Protocol.get(Protocol.uri == flow["process"].get("uri"))
        else:
            instance_name = flow["process"]["instance_name"] 
            proto = Protocol(instance_name=instance_name, user=user)
            proto.set_title(flow["process"]["title"])
            proto.set_layout(flow.get("layout",{}))
         
        if not proto.is_validated:
            
            # add process
            # -------------------------------------------
            for instance_name in flow["jobs"]:
                current_job = flow["jobs"][instance_name]
                
                if instance_name in proto._processes:
                    proc = proto._processes[instance_name]
                else:
                    # create and add a new process for this job
                    t_str = current_job["process"]["type"]
                    try:
                        t = Controller.get_model_type(t_str)
                    except:
                        raise Error("Protocol","from_flow", f"The subprotocol or subprocess type {t_str} is not found on the lab. Please ensure that the lab fullfil the requirements for this protocol.")
                    
                    proc_uri = current_job["process"].get("uri")
                    if proc_uri:
                        #-> the sub-process exists -> OK!
                        proc = t.get(t.uri == proc_uri)
                        proto.add_process(instance_name, proc)  # add to protocol and set instance_name before
                        proc.set_title(current_job["process"]["title"])
                    else:
                        raise Error("Protocol","from_flow", f"The subprotocol or subprocess uri {proc_uri} is not found")
                
                # update config
                proc.config.set_params( current_job["config"]["params"] )
            
            # create interfaces and outerfaces
            # -------------------------------------------
            interfaces = {}
            outerfaces = {}
            for k in flow["process"]["interfaces"]:
                _to = graph["interfaces"][k]["to"]  #destination port of the interface
                proc_name = _to["node"]
                port_name = _to["port"]
                proc = proto._processes[proc_name]
                port = proc.input.ports[port_name]
                interfaces[k] = port

            for k in flow["process"]["outerfaces"]:
                _from = graph["outerfaces"][k]["from"]  #source port of the outerface
                proc_name = _from["node"]
                port_name = _from["port"]
                proc = proto._processes[proc_name]
                port = proc.output.ports[port_name]
                outerfaces[k] = port

            if interfaces:
                proto.__set_interfaces(interfaces)

            if outerfaces:
                proto.__set_outerfaces(outerfaces)

            # add connectors
            # -------------------------------------------
            for flw in flow["flows"]:
                proc_name = flw["from"]["process"]["instance_name"]
                lhs_port_name = flw["from"]["process"]["port"]
                lhs_proc = proto._processes[proc_name]
                
                proc_name = flw["to"]["process"]["instance_name"]
                rhs_port_name = flw["to"]["process"]["port"]
                rhs_proc = proto._processes[proc_name]
                
                lhs_port = lhs_proc>>lhs_port_name
                rhs_port = rhs_proc<<rhs_port_name
                
                if not lhs_port.is_right_connected_to(rhs_port):
                    connector = (lhs_port | rhs_port)
                    proto.add_connector(connector)
            
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

    def __init_on_end_event(self):
        """
        Attach method `_run_after_task` to all sink processes to ensure that this method is called after
        all inner processes have finished.
        """
        
        sinks = []
        for k in self._processes:
            proc = self._processes[k]
            if self.is_outerfaced_with(proc) or not proc.output.is_connected:
                sinks.append(proc)

        for proc in sinks:
            proc.on_end( self._run_after_task )
            
    # -- L --
    
    # -- P --
    
    # -- R --
    
    async def _run_before_task(self, *args, **kwargs):
        self.save()
        
        if self.is_running or self.is_finished:
            return
        
        self._set_inputs()

        if self.job.experiment is None:
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
    
    def save(self, *args, **kwargs):
        if self.is_validated:
            return True
            #raise Error("gws.model.Protocol", "save", f"The protocol is already validated")
            
        with DbManager.db.atomic() as transaction:
            try:
                for k in self._processes:
                    self._processes[k].save()

                if not self.is_saved():
                    Activity.add(
                        self.created_by, 
                        Activity.CREATE,
                        object_type = self.full_classname(),
                        object_uri = self.uri
                    )

                return super().save(*args, **kwargs)
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Protocol", "save", f"Could not save the protocol. Error: {err}")
        
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

        self.data['input_specs'] = self._input.as_json()

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        self.data['output_specs'] = self._output.as_json()

    def __set_interfaces(self, interfaces: dict):
        input_specs = {}
        for k in interfaces:
            input_specs[k] = interfaces[k]._resource_types

        self.__set_input_specs(input_specs)
        
        self._interfaces = {}
        for k in interfaces:
            source_port = self.input.ports[k]
            self._interfaces[k] = Interface(name=k, source_port=source_port, target_port=interfaces[k])

    def __set_outerfaces(self, outerfaces: dict):
        output_specs = {}
        for k in outerfaces:
            output_specs[k] = outerfaces[k]._resource_types

        self.__set_output_specs(output_specs)
        
        self._outerfaces = {}
        for k in outerfaces:
            target_port = self.output.ports[k]
            self._outerfaces[k] = Outerface(name=k, target_port=target_port, source_port=outerfaces[k])

        #self._outerfaces = outerfaces
    
    # -- V --
    
    def validate(self, user):
        if self.is_validated:
            raise Error("gws.model.Protocol", "save", f"The Protocol is already validated")
        
        with DbManager.db.atomic() as transaction:
            try:
                Activity.add(
                    user,
                    Activity.VALIDATE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )

                self.is_validated = True
                self.save()
            except:
                transaction.rollback()
                raise Error("gws.model.Protocol", "save", f"Could not validate the protocol. Error: {err}")
            

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

    job = ForeignKeyField(Job, null=True, backref='resources')

    _table_name = 'gws_resource'

    # -- A --

    def archive(self, tf: bool):
        if self.is_archived == tf:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                tf = self.job.archive(tf) and super().archive(tf)
                if not tf:
                    transaction.rollback()
                    return False
                else:
                    return True
            except:
                transaction.rollback()
                return False

    def as_json(self, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().as_json(**kwargs)

        if not self.job is None:
            _json.update({
                "job_uri": self.job.uri,
                "experiment_uri": self.job.experiment.uri,
            })
  
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
    
    # -- D --

    def remove(self):
        if self.is_deleted:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                tf = self.job.remove() and super().remove()
                if not tf:
                    transaction.rollback()
                    return False
                else:
                    return True
            except:
                transaction.rollback()
                return False
    
    # -- E --
    
    def _export(self, file_path: str, file_format:str = None):
        """ 
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: str
        """
        
        #@ToDo: ensure that this method is only called by an Exporter
        
        pass
    
    # -- I --
    
    @classmethod
    def _import(cls, file_path: str, file_format:str = None) -> any:
        """ 
        Import a give from repository

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
    
    # -- S --
    
    def _select(self, **params) -> 'Model':
        """ 
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Selector
        
        pass
    
    def _set_job(self, job: 'Job'):
        """ 
        Sets the process of the resource.

        :param process: The process
        :type process: Process
        """

        if not isinstance(job, Job):
            raise Error("gws.model.Resource", "_set_job", "The job must be an instance of Job.")

        self.job = job

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
    
    def remove(self, key):
        del self._set[key]

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
        if self.is_saved() and len(self._set) == 0:
            for k in self.data["set"]:
                uri = self.data["set"][k]["uri"]
                rtype = self.data["set"][k]["type"]
                self._set[k] = Controller.fetch_model(rtype, uri)
        
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

    model_uri: str = CharField(index=True)
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

    def as_json(self, stringify: bool=False, prettify: bool=False) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().as_json()
        _json["model"] = self.model.as_json( **self.params )
        
        del _json["model_uri"]
        del _json["model_type"]
        del _json["param_hash"]
        
        if not self.is_saved():
            _json["uri"] = ""
            _json["save_datetime"] = ""
            
        #SOLUTION 1: clean and rigorous solution
        #_json = {
        #    "uri": self.uri if is_saved else None,
        #    "type": self.type,
        #    "data" : self.data,
        #    "model": self.model.as_json( **self.params ),
        #    "creation_datetime" : str(self.creation_datetime),
        #}
        
        #SOLUTION 2: easy usage, but less rigorous
        #_json = self.model.as_json( **self.params )
        #_json["view_model"] = {
        #    "uri": self.uri if is_saved else None,
        #    "type": self.type,
        #    "data" : self.data,
        #    "creation_datetime" : str(self.creation_datetime),
        #}

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- C --

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
    
    def get_instance( model, params ):
        
        try:
            h = self.__create_param_hash(params)
            vm = ViewModel.get( (ViewModel.mode_uri==model.uri) & (ViewModel.mode_type==model.type) & (ViewModel.param_hash==h) )
        except:
            vm = ViewModel(model=model)
            vm.set_params(params)
            
        return vm
    
    def get_param(self, key: str, default=None) -> str:
        return self.data["params"].get(key, default)
    
    def get_description(self) -> str:
        """
        Returns the description
        
        :return: The description
        :rtype: str
        """
        
        return self.data.get("description", "")
    
    def get_title(self) -> str:
        """ 
        Get the title.
        """
        
        return self.data.get("title", "")
    
    # -- H --
    
    @staticmethod
    def __create_param_hash(params):
        params = sort_dict_by_key(params)
        h = hashlib.md5()
        h.update( json.dumps(params).encode() )
        return h.hexdigest()
            
    # -- M --

    @property
    def model(self):
        if not self._model is None:
            return self._model

        model_t = Controller.get_model_type(self.model_type)
        model = model_t.get(model_t.uri == self.model_uri)
        self._model = model.cast()
        return self._model
    
    # -- P -- 
    
    @property
    def params(self):
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
        if not self.model_uri is None:
            raise Error("gws.model.ViewModel", "set_model", "A model already exists")
        
        self._model = model

        if model.is_saved():
            self.model_uri = model.uri

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
            if not self.model_uri is None and self._model.uri != self.model_uri:
                raise Error("gws.model.ViewModel", "save", "It is not allowed to change model of the ViewModel that is already saved")
                
            with DbManager.db.atomic() as transaction:
                try:
                    if self._model.save(*args, **kwargs):
                        self.model_uri = self._model.uri
                        self.model_type = self._model.full_classname()
                        
                        # hash params
                        params = sort_dict_by_key(self.params)
                        self.set_params(params)
                        self.param_hash = self.__create_param_hash( params )
                        
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

    
    class Meta:
        indexes = (
            # create a unique on model_uri,model_type,param_hash
            (('model_uri', 'model_type', 'param_hash'), True),
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