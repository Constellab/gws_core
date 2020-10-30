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

from datetime import datetime
from peewee import SqliteDatabase, Model as PWModel
from peewee import  Field, IntegerField, FloatField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField, IPField      
from playhouse.sqlite_ext import JSONField

from gws.logger import Logger
from gws.settings import Settings
from gws.store import KVStore
#from gws.session import Session

from gws.base import slugify, BaseModel, DbManager
from gws.base import format_table_name
from gws.controller import Controller
from gws.view import ViewTemplate, HTMLViewTemplate, JSONViewTemplate
from gws.io import Input, Output, InPort, OutPort, Connector
from gws.event import EventListener

# ####################################################################
#
# SystemTrackable class
#
# ####################################################################
 
class SystemTrackable:
    """
    SystemTrackable class representing elements that can only be create by the system.
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
    is_deleted = BooleanField(default=False, index=True)

    _kv_store: KVStore = None
    _uuid = None
    _uri_delimiter = "$"
    _is_deletable = True

    _table_name = 'model'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uuid = str(uuid.uuid4())

        if self.data is None:
            self.data = {}

        # ensures that field type is allways equal to the name of the class
        if self.type is None:
            self.type = self.full_classname()
        elif self.type != self.full_classname():
            # allow object cast after ...
            pass

        self._init_store()

        #Controller._register_model_specs(type(self))

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database

        :return: The model
        :rtype: `Model` instance
        """
        type_str = slugify(self.type)
        new_model_t = Controller.get_model_type(type_str)

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

    # -- D --

    def delete(self) -> bool:
        if not self._is_deletable:
            return False

        self.is_deleted = True
        return self.save()

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
   
    # -- G --

    @classmethod
    def get_by_uri(cls, uri: str) -> str:
        try:
            return cls.get(cls.uri == uri)
        except:
            return None

    @classmethod
    def get_uri_name(cls) -> str:
        """ 
        Returns the uri_name of the model

        :return: The uri_name
        :rtype: str
        """
        return cls.full_classname(slugify=True)


    def __generate_uri(self) -> str:
        """ 
        Generates the uri of the model

        :return: The uri
        :rtype: str
        """
        return self.get_uri_name() + Model._uri_delimiter + str(self.id)

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

    def _init_store(self):
        """ 
        Sets the object storage interface
        """
        self._kv_store = KVStore(self.store_path)

    # -- K --

    @property
    def store(self):
        return self._kv_store

    # -- P --

    @classmethod
    def parse_uri(cls, uri: str) -> list:
        """ 
        Parses the uri of a model and returns the corresponding `uri_name` an `uri_id`

        :param uri: The uri to parse
        :type uri: str
        :return: A list containing the uri_name and uri_id
        :rtype: list
        """

        tab = uri.split(cls._uri_delimiter)
        if len(tab) == 1:
            tab.append(0)
        return tab

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

    # -- T --

    def fetch_type_by_id(self, id) -> type:
        """ 
        Fecth the model type (string) by its `id` from the database and return the corresponding python type.
        Use the proper table even if the table name has changed.

        :param id: The id of the model
        :type id: int
        :return: The model type
        :rtype: type
        :Logger.error(Exception: If no model is found)
        """
        cursor = DbManager.db.execute_sql(f'SELECT type FROM {self._table_name} WHERE id = ?', str(id))
        row = cursor.fetchone()
        if len(row) == 0:
            Logger.error(Exception("Model", "fetch_type_by_id", "The model is not found."))
        type_str = row[0]
        model_t = Controller.get_model_type(type_str)
        return model_t

    # -- U --

    @property
    def uri_id(self) -> str:
        """ 
        Returns the uri_id of the model

        :return: The uri_id
        :rtype: str
        """
        return self.id

    # -- S --

    @property
    def store_path(self) -> str:
        """ 
        Returns the path of the KVStore of the model

        :return: The path of the KVStore
        :rtype: str
        """
        settings = Settings.retrieve()
        db_dir = settings.get_data("db_dir")

        if self.uri is None:
            return None
        else:
            return os.path.join(db_dir, 'store', self.uri)

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
            Logger.error(Exception(self.classname(),"set_data","The data must be a JSONable dictionary")  )
    
    def save(self, *args, **kwargs) -> bool:
        """ 
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input data is not a `dict`
        """
        if not self.table_exists():
            self.create_table()

        self.save_datetine = datetime.now()
        tf = super().save(*args, **kwargs)

        if self.uri is None:
            self.uri = self.__generate_uri()
            self._kv_store.connect(self.store_path)
            tf = self.save()
            
        return tf
    
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
                Logger.error(Exception("Model", "save_all", f"Error message: {err}"))

        return True

    # -- W --

# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):
    """
    Viewable class.

    :property _vmodel_specs: The list of registered view model types.
    :type specs: dict
    """

    _vmodel_specs: dict = {}

    def as_json(self) -> str:
        """
        Returns JSON (a dictionnary) representation of the model.

        :return: The JSON dictionary 
        :rtype: dict
        """
        return json.dumps({
            "id" : self.id,
            "data" : self.data,
            "uri": self.uri,
            "creation_datetime" : str(self.creation_datetime),
        })

    def as_html(self) -> str:
        """
        Returns HTML representation of the model

        :return: The HTML text
        :rtype: str
        """
        return "<x-gws class='gws-model' id='{}' data-id='{}' data-uri='{}'></x-gws>".format(self._uuid, self.id, self.uri)

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

    def create_vmodel_by_name(self, type_name: str):
        """
        Creates an instance of a registered ViewModel

        :param type_name: The slugified type name of the view model to create
        :type type_name: str
        :return: The created view model
        :rtype: ViewModel
        :raises Exception: If the view model cannot be created
        """

        if not isinstance(type_name, str):
            Logger.error(Exception(self.classname(), "create_vmodel_by_name", "The view name must be a string"))
        
        if type_name == HTMLViewModel.get_uri_name():
            vmodel_t = HTMLViewModel
        elif type_name == JSONViewModel.get_uri_name():
            vmodel_t = HTMLViewModel
        else:
            vmodel_t = self._vmodel_specs.get(type_name, None)

        if isinstance(vmodel_t, type):
            vmodel = vmodel_t(model=self)
            return vmodel
        else:
            Logger.error(Exception(self.classname(), "create_vmodel_by_name", f"The vmodel '{vmodel_t}' is not found"))

    # -- D --

    def delete(self):
        if self.is_deleted:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                Q = ViewModel.select().where( ViewModel.model_id == self.id )
                for vm in Q:
                    if not vm.delete():
                        transaction.rollback()
                        return False
                
                if super().delete():
                    return True
                else:
                    transaction.rollback()
                    return False
            except:
                transaction.rollback()
                return False

    # -- R -- 

    @classmethod
    def register_vmodel_specs(cls, specs: list):
        """
        Registers a list of view model types

        :param specs: List of view model types
        :type specs: list
        """
        for t in specs:
            if not isinstance(t, type) or not issubclass(t, ViewModel):
                Logger.error(Exception("Model", "register_vmodel_specs", "Invalid specs. A list of ViewModel types is expected"))
            
            name = t.full_classname(slugify=True)
            cls._vmodel_specs[name] = t

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

    _table_name = 'config'

    def __init__(self, *args, specs: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        if self.id is None:
            self.data = {
                "specs": {},
                "params": {}
            }
            
        if not specs is None:
            if not isinstance(specs, dict):
                Logger.error(Exception(self.classname(), "__init__", f"The specs must be a dictionnary"))
            
            #convert type to str
            from gws.validator import Validator
            for k in specs:
                if isinstance(specs[k]["type"], type):
                    specs[k]["type"] = specs[k]["type"].__name__ 

                default = specs[k].get("default", None)
                if not default is None:
                    param_t = specs[k]["type"]
                    try:
                        validator = Validator.from_type(param_t)
                        default = validator.validate(default)
                        specs[k]["default"] = default
                    except Exception as err:
                        Logger.error(Exception(self.classname(), "__init__", f"Invalid default config value. Error message: {err}"))

            self.set_specs( specs )

    # -- D --

    def delete(self):
        if self.is_deleted:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.process_id == self.id )
                for job in Q:
                    if not job.delete():
                        transaction.rollback()
                        return False
                
                if super().delete():
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
            Logger.error(Exception(self.classname(), "get_param", f"Parameter {name} does not exist'"))
        
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
            Logger.error(Exception(self.classname(), "set_param", f"Parameter '{name}' does not exist."))
        
        param_t = self.specs[name]["type"]

        try:
            validator = Validator.from_type(param_t)
            value = validator.validate(value)
        except Exception as err:
            Logger.error(Exception(self.classname(), "set_param", f"Invalid parameter value '{name}'. Error message: {err}"))

        self.data["params"][name] = value

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
        :Logger.error(Exception: If the config is already saved)
        """
        if not isinstance(specs, dict):
            Logger.error(Exception(self.classname(), "set_specs", f"The specs must be a dictionary."))
        
        if not self.id is None:
            Logger.error(Exception(self.classname(), "set_specs", f"Cannot alter the specs of a saved config"))
        
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
    
    :property config_id: The id of the process config
    :type config_id: bool
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

    hash = CharField(index=True, unique=True)
    is_running: bool = False 
    is_finished: bool = False 

    input_specs: dict = {}
    output_specs: dict = {}
    config_specs: dict = {}

    _event_listener: EventListener = None
    _unique_hash = "code"
    _input: Input
    _output: Output
    _table_name = 'process'
    _is_deletable = False

    _job: 'Job' = None  #ref to the current job

    def __init__(self, *args, name: str=None,  **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.id is None:
            self.hash = self.__create_hash()
            cls = type(self)
            try:
                proc = cls.get(cls.hash == self.hash)
                self.id = proc.id
            except:
                self.save()
                proc = cls.get(cls.hash == self.hash)
                self.id = proc.id
        else:
            self.__check_hash()

        if not name is None:
            self.data['name'] = name

        self._input = Input(self)
        self._output = Output(self)

        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        self._event_listener = EventListener()

    # -- A --

    def add_event(self, name, callback):
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
            Logger.error(Exception("Process", "add_event", f"Cannot add event. Error message: {err}"))

    # -- C --

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
        return self.get_active_job().config

    def __check_hash(self):
        actual_hash = self.__create_hash()
        if self.hash and self.hash != actual_hash:
            Logger.error(Exception("Process", "__set_hash", "Invalid process hash. The code source of the current process has changed."))

    def __create_hash(self):
        type_str = slugify(self.type)
        model_t = Controller.get_model_type(type_str)
        source = inspect.getsource(model_t)
        return self._unique_hash + ":" + self._hash_encode(source)
    
    # -- G --

    def get_param(self, name: str) -> [str, int, float, bool]:
        """
        Returns the value of a parameter of the process config by its name.

        :return: The paremter value
        :rtype: [str, int, float, bool]
        """
        return self.config.get_param(name)

    def get_active_job(self):
        """
        Initialize an job for the process.

        :return: The job
        :rtype: Job
        """

        if self._job is None:
            config = Config(specs = self.config_specs)
            self._job = Job(process=self, config=config)

        return self._job

    # -- H --

    @classmethod
    def _hash_encode(cls, data: str):
        hash_object = hashlib.sha512(data.encode())
        return hash_object.hexdigest()

    # -- I --

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
        return  (not self.is_running or \
                not self.is_finished) and \
                self._input.is_ready 

    def in_port(self, name: str) -> InPort:
        """
        Returns the port of the input by its name.

        :return: The port
        :rtype: InPort
        """
        if not isinstance(name, str):
            Logger.error(Exception(self.classname(), "in_port", "The name of the input port must be a string"))
        
        if not name in self._input._ports:
            Logger.error(Exception(self.classname(), "in_port", f"The input port '{name}' is not found"))

        return self._input._ports[name]

    # -- L --

    def __lshift__(self, name: str) -> InPort:
        """
        Alias of :meth:`in_port`.

        Returns the port of the input by its name
        :return: The port
        :rtype: InPort
        """
        return self.in_port(name)

    # -- N --

    @property
    def name(self) -> str:
        """ 
        Returns the context name of the process.

        :return: The name
        :rtype: str
        """
        return self.data.get("name","")

    @name.setter
    def name(self, name: str) -> str:
        """ 
        Returns the context name of the process.

        :return: The name
        :rtype: str
        """
        self.data["name"] = name

    def get_next_procs(self) -> list:
        """ 
        Returns the list of (right-hand side) processes connected to the IO ports.

        :return: List of processes
        :rtype: list
        """
        return self._output.get_next_procs()

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
            Logger.error(Exception(self.classname(), "out_port", "The name of the output port must be a string"))
        
        if not name in self._output._ports:
            Logger.error(Exception(self.classname(), "out_port", f"The output port '{name}' is not found"))

        return self._output._ports[name]

    def on_end(self, callback):
        """
        Adds an event to execute after the process ends running. 

        :param callback: The function to execute
        :callback: `function`
        """
        self.add_event('end', callback)

    def on_start(self, callback):
        """
        Adds an event to execute before the process starts running. 

        :param callback: The function to execute
        :callback: `function`
        """
        self.add_event('start', callback)

    # -- R -- 

    async def run(self):
        """ 
        Runs the process and save its state in the database.
        """

        try:
            self._run_before_task()
            self.task()
            self._run_after_task()
        except Exception as err:
            Logger.error(err)

    def _run_before_task( self, *args, **kwargs ):
        if self._event_listener.exists('pre_start'):
            self._event_listener.call('pre_start', self)

        self.is_running = True
        logger = Logger()
        if self.name:
            logger.info(f"Running {self.full_classname()} '{self.name}' ...")
        else:
            logger.info(f"Running {self.full_classname()} ...")
        
        if not self.is_ready:
            Logger.error(Exception(self.classname(), "run", "The process is not ready. Please ensure that the process receives valid input resources and has not already been run"))

        job = self.get_active_job()
        if not job.save():
            Logger.error(Exception(self.classname(), "run", "Cannot save the job"))
        
        if self._event_listener.exists('start'):
            self._event_listener.call('start', self)

    def _run_after_task( self, *args, **kwargs ):

        logger = Logger()
        if self.name:
            logger.info(f"Task of {self.full_classname()} '{self.name}' successfully finished!")
        else:
            logger.info(f"Task of {self.full_classname()} successfully finished!")

        self.is_running = False
        self.is_finished = True

        job = self.get_active_job()
        job.update_state()
        if not job.save():
            logger.error(Exception(self.classname(), "_run_after_task", f"Cannot save the job"))

        res = self.output.get_resources()
        for k in res:
            if not res[k] is None:
                res[k]._set_job(job)
                res[k].save()
        
        if not self._output.is_ready:
            return
            #Logger.error(Exception(self.classname(), "run", "The output was not set after the task ended."))
        
        if self._event_listener.exists('end'):
            self._event_listener.call('end', self)

        self._output.propagate()
        
        for proc in self._output.get_next_procs():
            asyncio.create_task( proc.run() )

    def __rshift__(self, name: str) -> OutPort:
        """ 
        Alias of :meth:`out_port`.
        
        Returns the port of the output by its name
        :return: The port
        :rtype: OutPort
        """
        return self.out_port(name)     
        
    # -- S --

    def set_input(self, name: str, resource: 'Resource'):
        """ 
        Sets the resource of an input port by its name.

        :param name: The name of the input port 
        :type name: str
        :param resource: A reources to assign to the port
        :type resource: Resource
        """
        if not isinstance(name, str):
            Logger.error(Exception(self.classname(), "set_input", "The name must be a string."))
        
        if not isinstance(resource, Resource):
            Logger.error(Exception(self.classname(), "set_input", "The resource must be an instance of Resource."))

        self._input[name] = resource
        
    def set_config(self, config: 'Config'):
        """ 
        Sets the config of the process.

        :param config: A config to assign
        :type config: Config
        """

        if isinstance(config, Config):
            self.config = config
        else:
            Logger.error(Exception(self.classname(), "set_config", "The config must be an instance of Config."))

    def set_param(self, name: str, value: [str, int, float, bool]):
        """ 
        Sets the value of a config parameter.

        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """
        self.config.set_param(name, value)

    def task(self):
        pass

# ####################################################################
#
# User class
#
# ####################################################################

class User(Model):

    token = CharField()
    is_admin = BooleanField(default=False, index=True)
    is_active = BooleanField(default=True, index=True)
    is_locked = BooleanField(default=False, index=True)
    is_authenticated = False

    _is_deletable = False
    _table_name = 'user'

    # -- G --
    
    def __generate_token(self):
        hash_object = hashlib.sha512(
            (self.uri + str(self.creation_datetime)).encode()
        )
        self.token = hash_object.hexdigest()
    
    # -- S --

    def save(self, *arg, **kwargs):
        if self.id is None:
            if self.token is None:
                self.__generate_token()

        return super().save(*arg, **kwargs)

    @classmethod
    def verify_user_token(cls, uri: str, token: str) -> ('User', bool,):
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

class Experiment(Model):
    
    protocol_id = IntegerField(null=False, index=True)       # store id ref as it may represent different classes
    score = FloatField(null=True, index=True)
    is_in_progress = BooleanField(default=True, index=True)
    _table_name = 'experiment'

    # -- D --

    def delete(self):
        if self.is_deleted:
            return True
            
        with DbManager.db.atomic() as transaction:
            try:
                Q = Job.select().where( Job.process_id == self.id )
                for job in Q:
                    if not job.delete():
                        transaction.rollback()
                        return False
                
                if super().delete():
                    return True
                else:
                    transaction.rollback()
                    return False
                    
            except:
                transaction.rollback()
                return False

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

    # -- P --

    @property 
    def protocol(self):
        return Protocol.get_by_id(self.protocol_id)

    # -- R --

    def run(self):
        self.protocol.run()

# ####################################################################
#
# Job class
#
# ####################################################################

class Job(Model, SystemTrackable):
    """
    Job class.

    :property process: The process of the job
    :type process: Process
    :property config: The config of the job's process
    :type config: Config
    :property user: The user
    :type user: User
    """
    
    process_id = IntegerField(null=False, index=True)       # store id ref as it may represent different classes
    config_id = IntegerField(null=False, index=True)        # store id ref as it may represent config classes
    experiment = ForeignKeyField(Experiment, null=True, backref='jobs')     #only valid for protocol
    is_running: bool = BooleanField(default=False, index=True)
    is_finished: bool = BooleanField(default=False, index=True)
    _process = None
    _config = None
    _table_name = 'job'

    def __init__(self, *args, process: Process = None, config: Config = None, **kwargs):
        super().__init__(*args, **kwargs)

        if self.id is None:
            if not isinstance(config, Config):
                Logger.error(Exception("Job", "__init__", "The config must be an instance of Config"))
 
            if not isinstance(process, Process):
                Logger.error(Exception("Job", "__init__", "The process must be an instance of Process"))
            
            self._config = config
            self._process = process
            self.update_state()

    # -- C --

    @property
    def config(self):
        """
        Returns the config fo the job.

        :return: The config
        :rtype: Config
        """

        if not self._config is None:
            return self._config

        if self.config_id:
            config = Config.get(Config.id == self.config_id)
            self._config = config.cast()
            return self._config
        else:
            return None

    # -- D --

    def delete(self):
        if self.is_deleted:
            return True

        return super().delete()

    # -- P --

    @property
    def process(self):
        """
        Returns the process fo the job.

        :return: The config
        :rtype: Config
        """

        if not self._process is None:
            return self._process

        if self.process_id:
            proc = Process.get(Process.id == self.process_id)
            self._process = proc.cast()
            return self._process
        else:
            return None

    # -- S --

    def update_state(self):
        """ 
        Update the state of the job
        """

        self.is_running = self.process.is_running
        self.is_finished = self.process.is_finished

    def set_experiment(self, experiment: 'Experiment'):
        if not isinstance(experiment, Experiment):
            raise Exception("The experiment must be an instance of Experiment")

        if self.experiment is None:
            self.experiment = experiment
        else:
            raise Exception("An experiment is already defined")

    def save(self, *args, **kwargs):
        """ 
        Save the job 
        """

        with DbManager.db.atomic() as transaction:
            try:
                if self.process is None:
                    Logger.error(Exception("Job", "save", "Cannot save the job. The process is not saved."))
                
                if not self.config.save():
                    Logger.error(Exception("Job", "save", "Cannot save the job. The config cannnot be saved."))
                
                self.process_id = self._process.id
                self.config_id = self._config.id

                self.__track_input_uri()
                if not super().save(*args, **kwargs):
                    Logger.error(Exception("Job", "save", "Cannot save the job."))
                
                res = self.process.output.get_resources()
                for k in res:
                    if res[k] is None:
                        continue

                    if not res[k].is_saved():
                        if not res[k].save(*args, **kwargs):
                            Logger.error(Exception("Job", "save", f"Cannot save the resource output '{k}' of the job"))

                return True
            except Exception as err:
                transaction.rollback()
                Logger.error(Exception("Job", "save", f"Error message: {err}"))

    # -- T --

    def __track_input_uri(self):
        res = self.process.input.get_resources()
        self.data["inputs"] = {}
        for k in res:
            if res[k] is None:
                continue
            
            if not res[k].is_saved():
                Logger.error(Exception("Process", "__track_input_uri", "Cannot track input '{k}' uri. Please save the input resource before."))

            self.data["inputs"][k] = res[k].uri

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

    _processes = {}
    _connectors = []
    _interfaces = {}
    _outerfaces = {}
    _unique_hash = "graph"
    _table_name = 'protocol'

    #/!\ Write protocols in the 'process' table
    #_table_name = 'process'

    def __init__(self, *args, name: str = None, processes: dict = None, connectors: list = None, \
                interfaces: dict = None, outerfaces: dict = None, graph: (str, dict)=None,\
                **kwargs):

        super().__init__(*args, name = name, **kwargs)

        if processes is None:
            if not self.data.get("graph", None) is None:
                self.__loads( self.data["graph"] )
            elif isinstance(graph, str):
                self.__loads( json.loads(graph) )
            elif isinstance(graph, dict):
                self.__loads( graph )
            self.save()
        else:
            if not isinstance(processes, dict):
                Logger.error(Exception("Protocol", "__init__", "A dictionnary of processes is expected"))
            
            if not isinstance(connectors, list):
                Logger.error(Exception("Protocol", "__init__", "A list of connectors is expected"))

            # process
            for name in processes:
                proc = processes[name]
                proc.name = name    #set context name
                if not isinstance(proc, Process):
                    Logger.error(Exception("Protocol", "__init__", "The dictionnary of processes must contain instances of Process"))
            self._processes = processes

            # connectors
            for conn in connectors:
                if not isinstance(conn, Connector):
                    Logger.error(Exception("Protocol", "__init__", "The list of connector must contain instances of Connectors"))
            self._connectors = connectors

            # interfaces
            self.__set_interfaces(interfaces)
            self.__set_outerfaces(outerfaces)

        self.__set_pre_start_event()
        self.__set_on_end_event()

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
            Logger.error(Exception("Protocol", "add_process", "The protocol has already been run"))
       
        if not isinstance(process, Process):
            Logger.error(Exception("Protocol", "add_process", "The process must be an instance of Process"))

        self._processes[name] = process

    def add_connector(self, connector: Connector):
        """ 
        Adds a connector to the protocol.

        :param connector: The connector
        :type connector: Connector
        :Logger.error(Exception: It the processes of the connection do not belong to the protocol)
        """

        if self.is_finished or self.is_running:
            Logger.error(Exception("Protocol", "add_connector", "The protocol has already been run"))
        
        if not isinstance(connector, Connector):
            Logger.error(Exception("Protocol", "add_connector", "The connector must be an instance of Connector"))
        
        if  not connector.left_process in self._processes.values() or \
            not connector.right_process in self._processes.values():
            Logger.error(Exception("Protocol", "add_connector", "The connector processes must be belong to the protocol"))
        
        if connector in self._connectors:
            Logger.error(Exception("Protocol", "add_connector", "Duplciated connector"))

        self._connectors.append(connector)

    # -- C --

    def __create_hash(self):
        graph = self.dumps()
        return self._unique_hash + ":" + self._hash_encode(graph)

    @classmethod
    def create_table(cls, *args, **kwargs):
        if not Experiment.table_exists():
            Experiment.create_table()
        
        if not Config.table_exists():
            Config.create_table()

        super().create_table(*args, **kwargs)

    # -- D -- 

    def dumps( self, as_dict = False, prettify = False ) -> str:
        """ 
        Returns the protocol graph
        """

        graph = dict(
            name = self.name,
            nodes = {},
            links = [],
            interfaces = {},
            outerfaces = {},
        )

        for conn in self._connectors:
            link = conn.to_json()
            is_left_node_found = False
            is_right_node_found = False
            for k in self._processes:
                if link["from"]["node"] is self._processes[k]:
                    link["from"]["node"] = k
                    is_left_node_found = True

                if link["to"]["node"] is self._processes[k]:
                    link["to"]["node"] = k
                    is_right_node_found = True
                
                if is_left_node_found and is_right_node_found:
                    graph['links'].append(link)
                    break

        for k in self._processes:
            graph["nodes"][k] = self._processes[k].full_classname()

        for k in self._interfaces:
            port = self._interfaces[k]
            proc = port.parent.parent
            for name in self._processes:
                if proc is self._processes[name]:
                    graph['interfaces'][k] = {"proc": name, "port": port.name}
                    break
        
        for k in self._outerfaces:
            port = self._outerfaces[k]
            proc = port.parent.parent
            for name in self._processes:
                if proc is self._processes[name]:
                    graph['outerfaces'][k] = {"proc": name, "port": port.name}
                    break
        
        if as_dict:
            return graph
        else:
            if prettify:
                return json.dumps(graph, indent=4)
            else:
                return json.dumps(graph)

    # -- G --

    def get_active_experiment(self):
        return self.get_active_job().experiment

    def get_process(self, name: str) -> Process:
        """ 
        Returns a process by its name.

        :return: The process
        :rtype": Process
        """
        return self._processes[name]

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
            port = self._interfaces[k] 
            if process is port.parent.parent:
                return True

        return False

    def is_outerfaced_with(self, process: Process) -> bool:
        """ 
        Returns True if the input poort the process is an outerface of the protocol
        """
        for k in self._outerfaces:
            port = self._outerfaces[k] 
            if process is port.parent.parent:
                return True

        return False

    # -- L --

    def __loads( self, graph: (str, dict) ) -> 'Protocol':
        """ 
        Construct a Protocol instance using a setting dump.

        :return: The protocol
        :rtype: Protocol
        """

        if isinstance(graph, str):
            graph = json.loads(graph)

        processes = {}
        connectors = []
        interfaces = {}
        outerfaces = {}

        self.name = graph.get("name", "")

        for k in graph["nodes"]:
            type_str = graph["nodes"][k]
            try:
                t = Controller.get_model_type(type_str)
            except Exception as err:
                raise Exception(f"The process {type_str} is not defined. The class module is probably not imported. Error: {err}")
            
            processes[k] = t()

        for link in graph["links"]:
            proc_name = link["from"]["node"]
            lhs_port_name = link["from"]["port"]
            lhs_proc = processes[proc_name]

            proc_name = link["to"]["node"]
            rhs_port_name = link["to"]["port"]
            rhs_proc = processes[proc_name]

            connector = (lhs_proc>>lhs_port_name | rhs_proc<<rhs_port_name)
            connectors.append(connector)

        for k in graph["interfaces"]:
            proc_name = graph["interfaces"][k]["proc"]
            port_name = graph["interfaces"][k]["port"]
            proc = processes[proc_name]
            port = proc.input.ports[port_name]
            interfaces[k] = port

        for k in graph["outerfaces"]:
            proc_name = graph["outerfaces"][k]["proc"]
            port_name = graph["outerfaces"][k]["port"]
            proc = processes[proc_name]
            port = proc.input.ports[port_name]
            outerfaces[k] = port

        self._processes = processes
        self._connectors = connectors

        self.__set_interfaces(interfaces)
        self.__set_outerfaces(outerfaces)

        self.data["graph"] = graph
        self.__create_hash()

    # -- R --
    
    async def run(self):
        """ 
        Runs the process and save its state in the database.
        Override mother class method.
        """

        if self.get_active_experiment() is None:
            raise Exception("No experiment defined for the active job of the protocol")

        self._run_before_task()

        # self.task()
        #---------- START OF BUILT-IN PROTOCOL TASK ---------

        sources = []
        for k in self._processes:
            proc = self._processes[k]
            if proc.is_ready or self.is_interfaced_with(proc):
                sources.append(proc)

        for proc in sources:
            await proc.run()

        #----------- END OF BUILT-IN PROTOCOL TASK ----------


    def _run_after_task(self, *args, **kwargs):
        # Exit the function if an inner process has not yet finished!
        for k in self._processes:
            if not self._processes[k].is_finished:
                return

        # Good! The protocol task is finished!
        self._set_outputs()
        super()._run_after_task()

    # -- S --

    def set_active_experiment(self, experiment: Experiment):
        job = self.get_active_job()
        job.set_experiment(experiment)

    def _set_inputs(self, *args, **kwargs):
        for k in self._interfaces:
            port = self._interfaces[k]
            port.resource = self.input[k]

    def _set_outputs(self, *args, **kwargs):
        for k in self._outerfaces:
            port = self._outerfaces[k]
            self.output[k] = port.resource

    def __set_pre_start_event(self):
        self._event_listener.add('pre_start', self._set_inputs)

    def __set_on_end_event(self):
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
            input_specs[k] = input_specs[k].__name__

        self.data['input_specs'] = input_specs

    def __set_output_specs(self, output_specs):
        self.output_specs = output_specs
        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        for k in output_specs:
            output_specs[k] = output_specs[k].__name__
        self.data['output_specs'] = output_specs

    def __set_interfaces(self, interfaces):
        if not interfaces is None:
            input_specs = { }
            for k in interfaces:
                input_specs[k] = interfaces[k]._resource_type

            self.__set_input_specs(input_specs)
            self._interfaces = interfaces

    def __set_outerfaces(self, outerfaces):
        if not outerfaces is None:
            output_specs = { }
            for k in outerfaces:
                output_specs[k] = outerfaces[k]._resource_type

            self.__set_output_specs(output_specs)
            self._outerfaces = outerfaces

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
    _table_name = 'resource'

    # -- D --

    def delete(self):
        if self.is_deleted:
            return True

        with DbManager.db.atomic() as transaction:
            try:
                tf = self.job.delete and super().delete()
                if not tf:
                    transaction.rollback()
                    return False
                else:
                    return True
            except:
                transaction.rollback()
                return False

        

    # -- S --

    def _set_job(self, job: 'Job'):
        """ 
        Sets the process of the resource.

        :param process: The process
        :type process: Process
        """

        if not isinstance(job, Job):
            Logger.error(Exception("Resource", "_set_job", "The job must be an instance of Job."))

        self.job = job

# ####################################################################
#
# ResourceSet class
#
# ####################################################################

class ResourceSet(Resource):
    
    _set = {}
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        if self.id is None:
            self.data["set"] = {}
            self._set = {}
        else:
            self._is_lazy = True
    
    def exists( self, resource ) -> bool:
        return resource in self._set

    def len(self):
        return self.len()

    def __len__(self):
        return len(self.set)

    def __getitem__(self, key):
        return self.set[key]

    def remove(self, key):
        del self._set[key]

    def __setitem__(self, key, val):
        if not isinstance(val, Resource):
            Logger.error(Exception("ResourceSet", "__setitem__", f"The value must be an instance of Resource. The actual value is a {type(val)}."))
        
        self.set[key] = val

    def save(self, *args, **kwrags):

        with DbManager.db.atomic() as transaction:
            try:
                self.data["set"] = {}
                for k in self._set:
                    if not (self._set[k].is_saved() or self._set[k].save()):
                        raise Exception("ResourceSet", "save", f"Cannot save the resource '{k}' of the resource set")
                        
                    self.data["set"][k] = self._set[k].uri

                return super().save(*args, **kwrags)

            except Exception as err:
                transaction.rollback()
                Logger.error(err)

    @property
    def set(self):
        if self.is_saved() and len(self._set) == 0:
            for k in self.data["set"]:
                uri = self.data["set"][k]
                self._set[k] = Controller.fetch_model(uri)
        
        return self._set

# ####################################################################
#
# Report class
#
# ####################################################################

class Report(Resource):
    pass

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
    _table_name = 'vmodel'

    def __init__(self, *args, model: Model = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if isinstance(model, Model):
            self._model = model
            self._model.register_vmodel_specs( [type(self)] )

        if not self.id is None:
            self._model = self.model

    # -- A --

    def as_json(self):
        """
        Returns a JSON (a dictionnary) representation of the view mode.

        :return: A JSON (dictionary)
        :rtype: dict
        """
        return {
            "id" : self.id,
            "data" : self.data,
            "uri": self.uri,
            "model": self.model.as_json(),
            "creation_datetime" : str(self.creation_datetime),
        }

    def as_html(self):
        """
        Returns HTML representation of the view model.

        :return: The HTML text
        :rtype: str
        """

        type_ = 'model'
        for model_t in self.model_specs:
            if self.get_uri_name() == model_t.get_uri_name():
                if issubclass(model_t, Process):
                    type_ = 'process'
                    break

        return f"<div class='gview:{self.get_uri_name()}' data-type='{type_}'>{self.as_json()}</div>"

    # -- C --

    # -- G --

    def get_view_url(self, params: dict={}) -> str:
        """
        Returns the uri of the view (alias of the uri of the view model).

        :param params: The uri parameters
        :type params: dict
        :return: The uri
        :rtype: str
        """
        if len(params) == 0:
            params = ""
        else:
            params = urllib.parse.quote(str(params))
        return '/read/' + self.uri + '/' + params

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

    def set_model(self, model: None):
        if not self.model_id is None:
            Logger.error(Exception(self.classname(),"save","A model already exists"))
        
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
            Logger.error(Exception(self.classname(),"set_template","The template must be an instance of ViewTemplate"))

        self.template = template
    
    def save(self, *args, **kwargs):
        """
        Saves the view model
        """
        if self._model is None:
            Logger.error(Exception(self.classname(),"save","The ViewModel has no model"))
        else:
            if not self.model_id is None and self._model.id != self.model_id:
                Logger.error(Exception(self.classname(),"save","It is not allowed to change model of the ViewModel that is already saved"))
                
            with DbManager.db.atomic() as transaction:
                try:
                    if self._model.save(*args, **kwargs):
                        self.model_id = self._model.id
                        self.model_type = self._model.full_classname()
                        return super().save(*args, **kwargs)
                    else:
                        Logger.error(Exception(self.classname(),"save","Cannot save the vmodel. Please ensure that the model of the vmodel is saved before"))
                except Exception as err:
                    transaction.rollback()
                    Logger.error(Exception("ViewModel", "save", f"Error message: {err}"))

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

    _table_name = 'vmodel'
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

    _table_name = 'vmodel'
    template = JSONViewTemplate("{{ vmodel.as_json() }}")

