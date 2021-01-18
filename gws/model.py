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

from base64 import b64encode, b64decode
from secrets import token_bytes

from datetime import datetime
from peewee import SqliteDatabase, Model as PWModel
from peewee import  Field, IntegerField, FloatField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField, IPField, TextField, BlobField
from playhouse.sqlite_ext import JSONField, SearchField, RowIDField

from gws.logger import Error, Info
from gws.store import KVStore
from gws.settings import Settings
from gws.base import slugify, BaseModel, BaseFTSModel, DbManager
from gws.base import format_table_name
from gws.controller import Controller
from gws.view import ViewTemplate, HTMLViewTemplate, JSONViewTemplate
from gws.io import Input, Output, InPort, OutPort, Connector, Interface, Outerface
from gws.event import EventListener
from gws.utils import to_camel_case

# ####################################################################
#
# SystemTrackable class
#
# ####################################################################
 
class SystemTrackable:
    """
    SystemTrackable class representing elements that can only be created by the core system.
    """
    pass

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
    :property save_datetine: The last save datetime in database
    :type save_datetine: datetime, `peewee.model.DateTimeField`
    :property data: The data of the model
    :type data: dict, `peewee.model.JSONField`
    """
    
    id = IntegerField(primary_key=True)
    uri = CharField(null=True, index=True)
    type = CharField(null=True, index=True)
    creation_datetime = DateTimeField(default=datetime.now)
    save_datetine = DateTimeField()    
    data = JSONField(null=True)
    is_archived = BooleanField(default=False, index=True)
    is_deleted = BooleanField(default=False, index=True)

    _kv_store: KVStore = None

    _is_singleton = False
    _is_deletable = True
    _fts_fields = {}

    _table_name = 'gws_model'

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

        self._kv_store = KVStore(self.kv_store_path)

    # -- A --

    def archive(self, status: bool) -> bool:
        if self.is_archived == status:
            return True
            
        self.is_archived = status
        return self.save()

    # -- C --

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database

        :return: The model
        :rtype: `Model` instance
        """

        #type_str = slugify(self.type)
        new_model_t = Controller.get_model_type(self.type)

        if type(self) == new_model_t:
            return self
   
        # instanciate the class and shallow copy data
        model = new_model_t()
        for prop in self.property_names(Field):
            val = getattr(self, prop)
            setattr(model, prop, val)

        return model

    def clear_data(self, save: bool = False):
        """
        Clears the :property:`data`

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
            raise Error("Model", "fetch_type_by_id", "The model is not found.")
        type_str = row[0]
        model_t = Controller.get_model_type(type_str)
        return model_t

    # -- G --

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
    def kv_store(self) -> KVStore:
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
            raise Error(cls.full_classname(), "search", "No FTSModel model defined")
        
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
            raise Error(self.classname(),"set_data","The data must be a JSONable dictionary")
    
    def set_data_value(self, key: str, value: str):
        """ 
        Sets the a given `data`

        :param key: The key
        :type key: srt
        :param value: The value
        :type value: any
        """
        self.data[key] = value

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
                            raise Exception(self.full_classname(), "save", "Cannot save related FTS document")

                #self.kv_store.save()
                self.save_datetine = datetime.now()
                return super().save(*args, **kwargs)
            except Exception as err:
                transaction.rollback()
                raise Error(self.full_classname(), "save", f"Error message: {err}")



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
                if model_list is None:
                    return
                
                for m in model_list:
                    if isinstance(m, cls):
                        m.save()
            except Exception as err:
                transaction.rollback()
                raise Error("Model", "save_all", f"Error message: {err}")

        return True

    # -- U --

     
# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):

    _vmodel_specs: dict = {}
    _fts_field = {'title': 2.0, 'description': 1.0}
    
    # -- A --

    def archive(self, status: bool):
        if self.is_archived == status:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                Q = ViewModel.select().where( ViewModel.model_id == self.id )
                for vm in Q:
                    if not vm.archive(status):
                        transaction.rollback()
                        return False
                
                if super().archive(status):
                    return True
                else:
                    transaction.rollback()
                    return False
            except:
                transaction.rollback()
                return False

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

        _json = {
            "uri": self.uri,
            "type": self.type,
            "data" : self.data,
            "creation_datetime" : str(self.creation_datetime),
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    def as_html(self) -> str:
        """
        Returns HTML representation of the model

        :return: The HTML text
        :rtype: str
        """
        return f"<div class='gview:model' json='true'>{self.as_json()}</div>"
    
    # -- C --

    def create_default_vmodel(self):
        if "default" in self._vmodel_specs:
            vmodel_t = self._vmodel_specs["default"]
            return vmodel_t(model=self)
        else:   
            for k in self._vmodel_specs:
                vmodel_t = self._vmodel_specs[k]
                return vmodel_t(model=self) #return the 1st vmodel

        return None
    
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
        Returns the description. Alias of :meth:`set_description`
        
        :param text: The description test
        :type text: str
        """
        
        if self.data is None:
            self.data = {}
            
        self.data["description"] = text

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

    @classmethod
    def register_vmodel_specs(cls, specs: list):
        """
        Registers a list of view model types

        :param specs: List of view model types
        :type specs: list
        """
        for t in specs:
            if not isinstance(t, type) or not issubclass(t, ViewModel):
                raise Error("Model", "register_vmodel_specs", "Invalid specs. A list of ViewModel types is expected")
            
            name = t.full_classname()
            cls._vmodel_specs[name] = t

    # -- S --

    def set_title(self, title: str):
        """ 
        Set the title

        :param title: The title
        :type title: str
        """
        
        self.data["title"] = title
        
    def set_description(self, text: str):
        """ 
        Set the description

        :param text: The description text
        :type text: str
        """
        
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
        
        if self.data is None:
            self.data = {}
            
        self.data["title"] = text
    
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
                raise Error(self.classname(), "__init__", f"The specs must be a dictionnary")
            
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
                        raise Error(self.classname(), "__init__", f"Invalid default config value. Error message: {err}")

            self.set_specs( specs )

    # -- A --

    def archive(self, status: bool):
        if self.is_archived == status:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.config_uri == self.uri )
                for job in Q:
                    if not job.archive(status):
                        transaction.rollback()
                        return False
                
                if super().archive(status):
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
            raise Error(self.classname(), "get_param", f"Parameter {name} does not exist'")
        
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
            raise Error(self.classname(), "set_param", f"Parameter '{name}' does not exist.")
        
        #param_t = self.specs[name]["type"]

        try:
            validator = Validator.from_specs(**self.specs[name])
            value = validator.validate(value)
        except Exception as err:
            raise Error(self.classname(), "set_param", f"Invalid parameter value '{name}'. Error message: {err}")
        
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
            raise Error(self.classname(), "set_specs", f"The specs must be a dictionary.")
        
        if not self.id is None:
            raise Error(self.classname(), "set_specs", f"Cannot alter the specs of a saved config")
        
        self.data = {
            "specs" : specs,
            "params" : {}
        }

# ####################################################################
#
# Process class
#
# ####################################################################

class Process(Viewable, SystemTrackable):
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

    def __init__(self, *args, instance_name: str=None, **kwargs):
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

        if 'title' in kwargs:
            self.set_title(kwargs['title'])
        
        if instance_name:
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
            raise Error("Process", "add_event", f"Cannot add event. Error message: {err}")
    
    def as_json(self, bare: bool=False, stringify: bool=False, prettify: bool=False) -> (str, dict, ):
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
        _json["input_specs"] = self.input.as_json(bare=bare)
        _json["output_specs"] = self.input.as_json(bare=bare)
        _json["config_specs"] = self.config_specs
        
        if bare:
            _json["uri"] = ""
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
    
    # -- C --
    
    def create_experiment(self, config: Config = None):
        if isinstance(config, Config):
            job = self.job
            job.set_config(config)
        
        instance_name = self.instance_name if self.instance_name else self.classname()
        proto = Protocol(processes={ 
            instance_name: self 
        })
        e = Experiment(protocol=proto)
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
        return  (not self.is_running and not self.is_finished) and self._input.is_ready 

    def in_port(self, name: str) -> InPort:
        """
        Returns the port of the input by its name.

        :return: The port
        :rtype: InPort
        """
        if not isinstance(name, str):
            raise Error(self.classname(), "in_port", "The name of the input port must be a string")
        
        if not name in self._input._ports:
            raise Error(self.classname(), "in_port", f"The input port '{name}' is not found")

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
            raise Error(self.classname(), "out_port", "The name of the output port must be a string")
        
        if not name in self._output._ports:
            raise Error(self.classname(), "out_port", f"The output port '{name}' is not found")

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
    
    #-- P --
    
    # -- R -- 

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
            raise Error("Process", "_run", f"Error: {err}")
    
    async def _run_next_processes(self):
        self._output.propagate()
        aws  = []
        job = self.job
        for proc in self._output.get_next_procs():
            # ensure that the next process is held by this experiment
            proc_job = proc.job
            proc_job.experiment = job.experiment
            proc_job.save()

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
        if not job.save():
            raise Error(self.classname(), "run", "Cannot save the job")
        
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
        job.update_status()
        if not job.save():
            raise Error(self.classname(), "_run_after_task", f"Cannot save the job")

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
    
    def set_instance_name(self, name:str ):
        if not self._instance_name:
            self._instance_name = name
        
        if self._instance_name != name:
            raise Error(self.classname(), "set_instance_name", "Try to set a different instance name")
            
    def set_input(self, name: str, resource: 'Resource'):
        """ 
        Sets the resource of an input port by its name.

        :param name: The name of the input port 
        :type name: str
        :param resource: A reources to assign to the port
        :type resource: Resource
        """
        if not isinstance(name, str):
            raise Error(self.classname(), "set_input", "The name must be a string.")
        
        if not isinstance(resource, Resource):
            raise Error(self.classname(), "set_input", "The resource must be an instance of Resource.")

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
            #self.config = config
        else:
            raise Error(self.classname(), "set_config", "The config must be an instance of Config.")

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

    def task(self):
        pass

# ####################################################################
#
# User class
#
# ####################################################################

class User(Model):
    
    token = CharField(null=False)
    is_admin = BooleanField(default=False, index=True)
    is_active = BooleanField(default=True, index=True)
    is_locked = BooleanField(default=False, index=True)

    is_authenticated = False

    _is_deletable = False
    _table_name = 'gws_user'
    _fts_fields = {'fullname': 2.0}

    # -- A --

    @classmethod
    def authenticate(cls, uri: str, token: str) -> ('User', bool,):
        """ 
        Verify the uri and token and returns the corresponding user 

        :param uri: The user uri
        :type uri: str
        :param token: The token to check
        :type token: str
        :return: The user if successfully verified, False otherwise
        :rtype: User, False
        """
        try:
            return User.get(User.uri==uri, User.token==token)
        except:
            return False

    # -- G --
    
    def get_fullname(self):
        return self.data.get("fullname", "")

    def __generate_token(self):
        return b64encode(token_bytes(32)).decode()
    
    def generate_access_token(self):
        self.token = self.__generate_token()
        self.save()

    # -- S --

    def save(self, *arg, **kwargs):
        if self.id is None:
            if self.token is None:
                self.token = self.__generate_token()

        return super().save(*arg, **kwargs)

    def set_fullname(self, fullname):
        self.data["fullname"] = fullname


    class Meta:
        indexes = (
            # create a unique on email,organization
            (('email', 'organization'), True),
        )

# ####################################################################
#
# UserLogin class
#
# ####################################################################

class UserLogin(Model):
    user = ForeignKeyField(User)
    status = BooleanField(index=True)
    ip_address = IPField()
    login_date = DateTimeField()
    _is_deletable = False

    def last_login(self, user):
        pass

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
    :property is_in_progress: True if the exepriment is in progress, False otherwiser
    :type is_in_progress: `bool`
    """
    
    protocol_uri = CharField(null=False, index=True)
    protocol_job_uri = CharField(null=False, index=True)
    score = FloatField(null=True, index=True)
    is_in_progress = BooleanField(default=True, index=True)
    
    _table_name = 'gws_experiment'
    
    _protocol = None
    _protocol_job = None

    def __init__(self, *args, protocol=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if isinstance(protocol, Protocol):
            if protocol.get_title():
                protocol.set_instance_name(protocol.get_title())
            else:
                protocol.set_instance_name(protocol.full_classname())
            
            if not protocol.is_saved():
                protocol.save()
            else:
                if not protocol.get_active_experiment() is None:
                    raise Error("Experiment", "__init__", "An experiment is already associated with the protocol")

            self.protocol_uri = protocol.uri
            self._protocol = protocol
            self._protocol.set_active_experiment(self)

    # -- A --
    
    def add_report(self, report: 'Report'):
        report.experiment = self

    def archive(self, status:bool):
        if self.is_archived == status:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.experiment == self )
                for job in Q:
                    if not job.archive(status):
                        transaction.rollback()
                        return False
                
                if super().archive(status):
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except:
                transaction.rollback()
                return False

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
        _json.update({
            "protocol_job_uri": self.protocol_job_uri,
            "score": self.score,
            "is_in_progress": self.is_in_progress,
        })
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json   
  
    # -- F --
    
    @property
    def flow(self):
        job = self.protocol_job
        return job.flow
    
    # -- J --

    # -- I --

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
    
    # -- O --

    def on_end(self, call_back: callable):
        self.protocol.on_end(call_back)
         
    def on_start(self, call_back: callable):
        self.protocol.on_start(call_back)
        
    # -- P --
    
    @property 
    def protocol(self):
        if not self._protocol:
            try:
                proto = Protocol.get(Protocol.uri == self.protocol_uri)
            except:
                raise Error("Experiment", "protocol", "The experiment has no protocol")
            
            self._protocol = proto.cast()

        return self._protocol
    
    @property 
    def protocol_job(self):
        if not self._protocol_job:
            try:
                self._protocol_job = Job.get(Job.uri == self.protocol_job_uri)
            except:
                raise Error("Experiment", "protocol_job", "The experiment has no job")
            
        return self._protocol_job
            
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

    async def run(self):
        self.job = self.protocol.job
        self.save()
        await self.protocol._run()
    
# ####################################################################
#
# Job class
#
# ####################################################################

class Job(Viewable, SystemTrackable):
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
    :property status: The status of experiment, 1 = is_running, 2 = is_finished, 0 otherwise
    :type status: integer 
    """
    
    parent_job = ForeignKeyField('self', null=True, backref='children')
    process_uri = CharField(null=False, index=True)                         # save id as it may represent different type of process
    process_type = CharField(null=False)                        
    process_source = BlobField(null=True)                  
    config_uri = CharField(null=False, index=True)                          # save id ref as it may represent config classes
    experiment = ForeignKeyField(Experiment, null=True, backref='jobs')     # only valid for protocol
    status = IntegerField(default=0, index=True)

    _process: Process = None
    _config: Config = None
    _table_name = 'gws_job'
    _fts_fields = {}
    
    def __init__(self, *args, process: Process = None, config: Config = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.id is None:
            if (not config is None) and (not isinstance(config, Config)):
                raise Error("Job", "__init__", "The config must be an instance of Config")
 
            if (not process is None) and (not isinstance(process, Process)):
                raise Error("Job", "__init__", "The process must be an instance of Process")
            
            self._config = config
            self._process = process
            self.update_status()
            
            if not process.instance_name:
                raise Error("Job", "__init__", "The process has no instance name.")
                
            self.data["instance_name"] = process.instance_name
            
    # -- A --

    def archive(self, status: bool):
        # /!\ Do not archive Config, Process and Experiment
        if self.is_archived == status:
            return True

        return super().archive(status)
    
    @property
    def instance_name(self) -> str:
        """
        Returns the instance name of the job (i.e. of the process) in the context of the current protocol.

        :return: The instance name
        :rtype: `str`
        """
        
        return self.data["instance_name"]
    
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
        
        if not self.parent_job is None:
            parent_job_uri = self.parent_job.uri
        else:
            parent_job_uri = None
            protocol = self.process
            if isinstance(protocol, Protocol):
                _json["layout"] = protocol.get_layout()
        
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
                "instance_name": self.instance_name, #do not use self.process.instance_name as it is not saved on db
                "input_specs": self.process.input.as_json(),
                "output_specs": self.process.output.as_json(),
                "config_specs": config_specs
            },
            "config": {
                "uri": self.config.uri,
                "type": self.config.type,
                "params": self.config.params,
            },
            "parent_job_uri": parent_job_uri,
            "experiment_uri": self.experiment.uri,
            "is_running": self.is_running,
            "is_finished": self.is_finished
        })
  
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- C --

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
            raise Error("Job", "dumps_flow", "The job must be related ot a protocol")     
        
        flow = self.as_json()
        if "data" in flow:
            del flow["data"]
            
        flow.update({
            "jobs": {},
            "flows": []
        })
    
        flow["layout"] = protocol.get_layout()
        flow["interfaces"] = {}
        flow["outerfaces"] = {}
        
        for k in protocol._interfaces:
            flow["interfaces"][k] = protocol._interfaces[k].as_json()
            
        for k in protocol._outerfaces:
            flow["outerfaces"][k] = protocol._outerfaces[k].as_json()

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
    
    @property
    def flow_old(self):
        if not self.is_finished:
            return {}
        
        if not len(self.children):
            return {}
        
        protocol = self.process
        
        if not isinstance(protocol, Protocol):
            raise Error("Job", "dumps_flow", "The job must be related ot a protocol")     
        
        flow = self.as_json()
        if "data" in flow:
            del flow["data"]
            
        flow.update({
            "jobs": {},
            "flows": []
        })
    
        flow["layout"] = protocol.get_layout()
        flow["interfaces"] = {}
        flow["outerfaces"] = {}
        
        for k in protocol._interfaces:
            flow["interfaces"][k] = protocol._interfaces[k].as_json()
            
        for k in protocol._outerfaces:
            flow["outerfaces"][k] = protocol._outerfaces[k].as_json()

        for job in self.children:
            flow["jobs"][job.uri] = job.as_json()

            for k in job.data["input"]:
                _input = job.data["input"][k]
                flow["flows"].append({
                    "to": {
                        "job_uri": job.uri,
                        "process": {
                            "uri": job.process.uri,
                            "instance_name": job.process.instance_name,
                            "port": k,
                        }
                    },
                    "from": _input["previous"],
                    "resource_uri": _input["resource_uri"]
                })

        return flow
    
    # -- G --

        
    # -- I --
    
    @property
    def is_running(self):
        return self.status == 1
    
    @is_running.setter
    def is_running(self, tf):
        if tf:
            self.status = 1
    
    @property
    def is_finished(self):
        return self.status == 2
    
    @is_finished.setter
    def is_finished(self, tf):
        if tf:
            self.status = 2
    
    # -- P --
    
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

    def update_status(self):
        """ 
        Update the state of the job
        """

        if self.process:
            self.is_running = self.process.is_running
            self.is_finished = self.process.is_finished

    def set_config(self, config: Config):
        if not config.is_saved():
            config.save()
            self.config_uri = config.uri
        self._config = config
        
    def set_experiment(self, experiment: 'Experiment'):
        if not isinstance(experiment, Experiment):
            raise Error("The experiment must be an instance of Experiment")
        
        if self.experiment is experiment:
            return
        
        if self.experiment is None:
            self.experiment = experiment
        else:
            raise Error("An experiment is already defined")

    def save(self, *args, **kwargs):
        """ 
        Save the job 
        """

        with DbManager.db.atomic() as transaction:
            try:
                if self.process is None:
                    raise Exception("Job", "save", "Cannot save the job. The process is not saved.")
                
                if not self.config.save():
                    raise Exception("Job", "save", "Cannot save the job. The config cannnot be saved.")
                
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
                            raise Exception("Job", "save", f"Cannot save the resource output '{k}' of the job")

                self.__track_input_uri()
                #self.__track_ouput_uri()
                if not super().save(*args, **kwargs):
                    raise Exception("Job", "save", "Cannot save the job.")
                
                return True
            except Exception as err:
                transaction.rollback()
                raise Error("Job", "save", f"An error occuured. Error: {err}")

    # -- T --
     
    def __track_input_uri(self):
        _input = self.process.input
        self.data["input"] = {}
        for k in _input.ports:
            port = _input.ports[k]
            res = port.resource

            if res is None:
                self.data["input"][k] = {
                    "resource_uri": ""
                }
            else:
                if not res.is_saved():
                    raise Error("Process", "__track_input_uris", f"Cannot track input '{k}' uri. Please save the input resource before.")
  
                is_interfaced = not port.is_left_connected

                if not is_interfaced:
                    left_port_name = port.prev.name
                    self.data["input"][k] = {
                        "resource_uri": res.uri,
                        "previous": {
                            "job_uri": res.job.uri,
                            "process": {
                                "uri": res.job.process.uri,
                                "instance_name": res.job.process.instance_name,
                                "port": left_port_name
                            }
                        }
                    } 
                else:
                    parent_job = self.parent_job
                    parent_protocol = self.process._parent_protocol

                    interface = parent_protocol.get_interface_of_target_port( port )
                    source_port = interface.source_port
  
                    if source_port.is_left_connected:
                        left_port_name = source_port.prev.name
                    else:
                        left_port_name = ""      

                    self.data["input"][k] = {
                        "resource_uri": res.uri,
                        "previous": {
                            "job_uri": res.job.uri,
                            "process": {
                                "uri": res.job.process.uri,
                                "instance_name": res.job.process.instance_name,
                                "port": left_port_name,
                            },
                            "interface": {
                                "port" : interface.name,
                            }
                        }
                    }                    
        
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
                    raise Error("Process", "__track_ouput_uri", f"Cannot track output '{k}' uri. Please save the output resource before.")

                self.data["output"][k] = {
                    "resource_uri": res.uri
                }
        
# ####################################################################
#
# Protocol class
#
# ####################################################################

class Protocol(Process, SystemTrackable):
    """ 
    Protocol class.

    :param processes: Dictionnary of processes
    :type processes: dict
    :param connectors: List of connectors represinting process connection
    :type connectors: list
    """

    type = CharField(null=True, index=True, unique=False)

    _is_singleton = False
    _processes: dict = None
    _connectors: list = []
    _interfaces: dict = None
    _outerfaces: dict = None
    _defaultPosition: list = [0, 0]
    
    _table_name = 'gws_protocol'

    def __init__(self, *args, processes: dict = None, \
                 connectors: list = [], interfaces: dict = {}, outerfaces: dict = {}, **kwargs):

        super().__init__(*args, **kwargs)

        self._processes = {}
        self._connectors = []
        self._interfaces = {}
        self._outerfaces = {}
        self._defaultPosition = [0, 0]

        if processes is None:
            if self and self.data.get("graph", None):  #the protocol was saved in the super classe
                self.__build_from_dump( self.data["graph"] )
        else:
            if not isinstance(processes, dict):
                raise Error("Protocol", "__init__", "A dictionnary of processes is expected")
            
            if not isinstance(connectors, list):
                raise Error("Protocol", "__init__", "A list of connectors is expected")

            # set process
            for name in processes:
                proc = processes[name]
                if not isinstance(proc, Process):
                    raise Error("Protocol", "__init__", "The dictionnary of processes must contain instances of Process")
            
                self.add_process(name, proc)

            # set connectors
            for conn in connectors:
                if not isinstance(conn, Connector):
                    raise Error("Protocol", "__init__", "The list of connector must contain instances of Connectors")
                
                self.add_connector(conn)
 
            # set interfaces
            self.__set_interfaces(interfaces)
            self.__set_outerfaces(outerfaces)
            
            self.data["graph"] = self.dumps(as_dict=True)
            self.save()

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
            raise Error("Protocol", "add_process", "The protocol has already been run")
       
        if not isinstance(process, Process):
            raise Error("Protocol", "add_process", f"The process '{name}' must be an instance of Process")

        if not process._parent_protocol is None:
            raise Error("Protocol", "add_process", f"The process instance '{name}' already belongs to another protocol")
        
        if name in self._processes:
            raise Error("Protocol", "add_process", f"Process name '{name}' already exists")
        
        if process in self._processes.items():
            raise Error("Protocol", "add_process", f"Process '{name}' duplicate")
            
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
            raise Error("Protocol", "add_connector", "The protocol has already been run")
        
        if not isinstance(connector, Connector):
            raise Error("Protocol", "add_connector", "The connector must be an instance of Connector")
        
        if  not connector.left_process in self._processes.values() or \
            not connector.right_process in self._processes.values():
            raise Error("Protocol", "add_connector", "The connector processes must be belong to the protocol")
        
        if connector in self._connectors:
            raise Error("Protocol", "add_connector", "Duplciated connector")

        self._connectors.append(connector)

    # -- C --

    def create_experiment(self, uri: str = None, config: Config = None):
        if self.get_title():
            self.set_instance_name(self.get_title())
        else:
            self.set_instance_name(self.full_classname())
        
        if isinstance(config, Config):
            job = self.job
            job.set_config(config)
        
        if uri:
            e = Experiment(uri=uri, protocol=self)
        else:
            e = Experiment(protocol=self)
            
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
        Dumps the JSON graph representing the protocol
        
        :param as_dict: If True, returns a dictionnary. A JSON string is returns otherwise
        :type as_dict: bool
        :param prettify: If True, the JSON string is indented.
        :type prettify: bool
        :param bare: If True, returns a bare dump i.e. the uris of the processes (and sub-protocols) of not returned. 
        Bare dumps allow creating a new protocols from scratch.
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
        
        proto = Protocol()
        proto.__build_from_dump(graph)
        proto.data["graph"] = proto.dumps(as_dict=True)
        proto.save()
        return proto
        
    # -- G --
    
    @property
    def graph(self):
        return self.data["graph"]
    
    def get_active_experiment(self):
        return self.job.experiment

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

    def get_interface_of_target_port(self, target_port: InPort) -> Interface:
        """ 
        Returns interface with a given target input port
        
        :param target_port: The InPort
        :type target_port: InPort
        :return: The interface, None otherwise
        :rtype": Interface
        """
        
        for k in self._interfaces:
            port = self._interfaces[k].target_port
            if port is target_port:
                return self._interfaces[k]

        return None
    
    def get_outerface_of_target_port(self, target_port: OutPort) -> Outerface:
        """ 
        Returns interface with a given target output port
        
        :param target_port: The InPort
        :type target_port: OutPort
        :return: The outerface, None otherwise
        :rtype": Outerface
        """
        
        for k in self._outerfaces:
            port = self._outerfacess[k].target_port
            if port is target_port:
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
            port = self._outerfaces[k].target_port
            if process is port.parent.parent:
                return True

        return False

    # -- L --

    def __build_from_dump( self, graph: (str, dict) ) -> 'Protocol':
        """ 
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """

        if isinstance(graph, str):
            graph = json.loads(graph)
        
        if len(graph) == 0:
            return
        
        self.set_title(graph.get("title",""))
        self.set_instance_name(graph.get("title",""))
        processes = {}
        connectors = []
        interfaces = {}
        outerfaces = {}
        
        # create nodes
        
        for k in graph["nodes"]:
            node_uri = graph["nodes"][k].get("uri",None)
            node_type_str = graph["nodes"][k]["type"]
            
            try:
                process_t = Controller.get_model_type(node_type_str)
                
                if process_t is None:
                    raise Exception(f"Process {node_type_str} is not defined. Please ensure that the corresponding brick is loaded.")
                else:
                    if node_uri:
                        processes[k] = process_t.get(process_t.uri == node_uri)
                    else:
                        processes[k] = process_t()
                    self.add_process( k, processes[k] )

            except Exception as err:
                raise Error(f"An error occured. Error: {err}")
        
        # create interfaces and outerfaces

        for k in graph["interfaces"]:
            _to = graph["interfaces"][k]["to"]  #destination port of the interface
            proc_name = _to["node"]
            port_name = _to["port"]
            proc = processes[proc_name]
            port = proc.input.ports[port_name]
            interfaces[k] = port

        for k in graph["outerfaces"]:
            _to = graph["outerfaces"][k]["to"]  #destination port of the outerface
            proc_name = _to["node"]
            port_name = _to["port"]
            proc = processes[proc_name]
            port = proc.output.ports[port_name]
            outerfaces[k] = port
            
        self.__set_interfaces(interfaces)
        self.__set_outerfaces(outerfaces)
        
        # create links
        
        for link in graph["links"]:
            proc_name = link["from"]["node"]
            lhs_port_name = link["from"]["port"]
            lhs_proc = processes[proc_name]

            proc_name = link["to"]["node"]
            rhs_port_name = link["to"]["port"]
            rhs_proc = processes[proc_name]

            connector = (lhs_proc>>lhs_port_name | rhs_proc<<rhs_port_name)
            connectors.append(connector)
            self.add_connector(connector)
    
    # -- P --
    
    # -- R --
    
    async def _run_before_task(self, *args, **kwargs):
        if self.is_running or self.is_finished:
            return
        
        self._set_inputs()
        
        e = self.get_active_experiment()
        if e is None:
            raise Error("Protocol", "_run", "No experiment defined")

        e.save()

        for k in self._processes:
            job = self._processes[k].job
            job.experiment = e
            job.save()
        
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
        e = self.get_active_experiment()
        e.is_in_progress = False
        e.save()

        self._set_outputs()
        await super()._run_after_task()

    # -- S --

    def set_active_experiment(self, experiment: Experiment):
        job = self.job
        job.set_experiment(experiment)
        experiment.protocol_job_uri = job.uri

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
            port = self._outerfaces[k].target_port
            self.output[k] = port.resource

    #def __init_pre_start_event(self):
    #    self._event_listener.add('pre_start', self._set_inputs)

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

    def __set_input_specs(self, input_specs):
        self.input_specs = input_specs
        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        for k in input_specs:
            for t in input_specs[k]:
                if t is None:
                    input_specs[k] = None
                else:
                    input_specs[k] = t.__name__

        self.data['input_specs'] = input_specs

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        for k in output_specs:
            for t in output_specs[k]:
                if t is None:
                    output_specs[k] = None
                else:
                    output_specs[k] = t.__name__
            
        self.data['output_specs'] = output_specs

    def __set_interfaces(self, interfaces: dict):
        input_specs = {}
        for k in interfaces:
            input_specs[k] = interfaces[k]._resource_types

        self.__set_input_specs(input_specs)

        for k in interfaces:
            source_port = self.input.ports[k]
            self._interfaces[k] = Interface(name=k, source_port=source_port, target_port=interfaces[k])

    def __set_outerfaces(self, outerfaces: dict):
        output_specs = {}
        for k in outerfaces:
            output_specs[k] = outerfaces[k]._resource_types

        self.__set_output_specs(output_specs)

        for k in outerfaces:
            source_port = self.output.ports[k]
            self._outerfaces[k] = Outerface(name=k, source_port=source_port, target_port=outerfaces[k])

        #self._outerfaces = outerfaces

# ####################################################################
#
# Resource class
#
# ####################################################################

class Resource(Viewable, SystemTrackable):
    """
    Resource class.
    
    :property process: The process that created he resource
    :type process: Process
    """

    job = ForeignKeyField(Job, null=True, backref='resources')

    _table_name = 'gws_resource'

    # -- A --

    def archive(self, status: bool):
        if self.is_archived == status:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                tf = self.job.archive(status) and super().archive(status)
                if not tf:
                    transaction.rollback()
                    return False
                else:
                    return True
            except:
                transaction.rollback()
                return False

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
        
        #@ToDo: ensure that this method is only called by an Importer
        
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
    
    # -- P --

    # -- S --

    def _set_job(self, job: 'Job'):
        """ 
        Sets the process of the resource.

        :param process: The process
        :type process: Process
        """

        if not isinstance(job, Job):
            raise Error("Resource", "_set_job", "The job must be an instance of Job.")

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
    
    def exists( self, resource ) -> bool:
        return resource in self._set

    def len(self):
        return self.len()
    
    def __contains__(self, val):
        return val in self.set
    
    def __len__(self):
        return len(self.set)

    def __getitem__(self, key):
        return self.set[key]

    def remove(self, key):
        del self._set[key]

    def __setitem__(self, key, val):
        if not isinstance(val, self._resource_types):
            raise Error("ResourceSet", "__setitem__", f"The value must be an instance of {self._resource_types}. The actual value is a {type(val)}.")
        
        self.set[key] = val

    def save(self, *args, **kwrags):

        with DbManager.db.atomic() as transaction:
            try:
                self.data["set"] = {}
                for k in self._set:
                    if not (self._set[k].is_saved() or self._set[k].save()):
                        raise Exception("ResourceSet", "save", f"Cannot save the resource '{k}' of the resource set")

                    self.data["set"][k] = {
                        "uri": self._set[k].uri,
                        "type": self._set[k].full_classname()
                    }    

                return super().save(*args, **kwrags)

            except Exception as err:
                transaction.rollback()
                raise Error("ResourceSet", "save", f"Error: {err}")

    @property
    def set(self):
        if self.is_saved() and len(self._set) == 0:
            for k in self.data["set"]:
                uri = self.data["set"][k]["uri"]
                rtype = self.data["set"][k]["type"]
                self._set[k] = Controller.fetch_model(rtype, uri)
        
        return self._set

# ####################################################################
#
# ViewModel class
#
# ####################################################################

class ViewModel(Model):
    """ 
    ViewModel class.

    :property model_id: Id of the Model of the ViewModel
    :type model: int
    :property model_type: Type of the Model of the ViewModel
    :type model_type: str
    :property template: The view template
    :type template: ViewTemplate
    :property model_specs: List containing the type of the default Models associated with the ViewModel.
    :type model_specs: list
    """

    model_id: int = IntegerField(index=True)
    model_type :str = CharField(index=True)
    model_specs: list = []
    template: ViewTemplate = None

    _model = None

    _table_name = 'gws_view_model'
    _fts_fields = {'title': 2.0, 'description': 1.0}

    def __init__(self, *args, model: Model = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if isinstance(model, Model):
            self._model = model
            self._model.register_vmodel_specs( [type(self)] )

        if not self.id is None:
            self._model = self.model

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
        
        _json = {
            "uri": self.uri,
            "type": self.type,
            "data" : self.data,
            "model": self.model.as_json(),
            "creation_datetime" : str(self.creation_datetime),
        }
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    def as_html(self):
        """
        Returns HTML representation of the view model.

        :return: The HTML text
        :rtype: str
        """

        return f"<div class='gview:model' json='true'>{self.as_json()}</div>"


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

    # -- M --

    @property
    def model(self):
        if not self._model is None:
            return self._model

        model_t = Controller.get_model_type(self.model_type)
        model = model_t.get(model_t.id == self.model_id)
        self._model = model.cast()
        return self._model
    
    # -- R --

    @classmethod
    def register_to_models(cls):
        for model_t in cls.model_specs:
            model_t.register_vmodel_specs( [cls] )

    def render(self, data: dict = None) -> str:
        """
        Renders the view of the view model.

        :param data: Rendering parameters
        :type data: dict
        :return: The rendering
        :rtype: str
        """
        if isinstance(data, dict):
            self.set_data(data)
  
        return self.template.render(self)
    
    # -- S --
    
    def set_description(self, text: str):
        """
        Returns the description.
        
        :param text: The description text
        :type text: `str`
        """
        
        self.data["description"] = text
    
    def set_model(self, model: None):
        if not self.model_id is None:
            raise Error(self.classname(),"save","A model already exists")
        
        self._model = model

        if model.is_saved():
            self.model_id = model.id


    def set_template(self, template: ViewTemplate):
        """
        Sets the view template.

        :param template: The view template
        :type template: ViewTemplate
        """
        if not isinstance(template, ViewTemplate):
            raise Error(self.classname(),"set_template","The template must be an instance of ViewTemplate")

        self.template = template
    
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
        if self._model is None:
            raise Error(self.classname(),"save","The ViewModel has no model")
        else:
            if not self.model_id is None and self._model.id != self.model_id:
                raise Error(self.classname(),"save","It is not allowed to change model of the ViewModel that is already saved")
                
            with DbManager.db.atomic() as transaction:
                try:
                    if self._model.save(*args, **kwargs):
                        self.model_id = self._model.id
                        self.model_type = self._model.full_classname()
                        return super().save(*args, **kwargs)
                    else:
                        raise Exception(self.classname(),"save","Cannot save the vmodel. Please ensure that the model of the vmodel is saved before")
                except Exception as err:
                    transaction.rollback()
                    raise Error("ViewModel", "save", f"Error message: {err}")
    
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
    

# ####################################################################
#
# HTMLViewModel class
#
# ####################################################################

class HTMLViewModel(ViewModel):
    """ 
    HTMLViewModel class.

    :property model: The model of the view model
    :type model: Process
    """

    template = HTMLViewTemplate("{{ vmodel.as_html() }}")

# ####################################################################
#
# JSONViewModel class
#
# ####################################################################

class JSONViewModel(ViewModel):
    """ 
    JSONViewModel class.

    :property model: The model of the view model
    :type model: Resource
    """

    template = JSONViewTemplate("{{ vmodel.as_json() }}")

