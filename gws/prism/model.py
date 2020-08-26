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

from datetime import datetime
from peewee import SqliteDatabase, Model as PWModel
from peewee import  Field, IntegerField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField             
from playhouse.sqlite_ext import JSONField

from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, \
                                JSONResponse, PlainTextResponse
from starlette.authentication import BaseUser

from gws.logger import Logger
from gws.settings import Settings
from gws.store import KVStore
from gws.prism.base import slugify
from gws.prism.base import Base, format_table_name
from gws.prism.controller import Controller
from gws.prism.view import ViewTemplate, ViewTemplateFile
from gws.prism.io import Input, Output, InPort, OutPort, Connector



class DbManager(Base):
    """
    DbManager class. Provides backend feature for managing databases. 
    """
    settings = Settings.retrieve()
    db = SqliteDatabase(settings.db_path)
    
    @staticmethod
    def create_tables(models: list, **options):
        """
        Creates the tables of a list of models. Wrapper of :meth:`DbManager.db.create_tables`
        :param models: List of model instances
        :type models: list
        :param options: Extra parameters passed to :meth:`DbManager.db.create_tables`
        :type options: dict, optional
        """
        DbManager.db.create_tables(models, **options)

    @staticmethod
    def drop_tables(models: list, **options):
        """
        Drops the tables of a list of models. Wrapper of :meth:`DbManager.db.drop_tables`
        :param models: List of model instances
        :type models: list
        :param options: Extra parameters passed to :meth:`DbManager.db.create_tables`
        :type options: dict, optional
        """
        DbManager.db.drop_tables(models, **options)

    @staticmethod
    def connect_db() -> bool:
        """
        Open a connection to the database. Reuse existing open connection if any. 
        Wrapper of :meth:`DbManager.db.connect`
        :return: True if the connection successfully opened, False otherwise
        :rtype: bool
        """
        return DbManager.db.connect(reuse_if_open=True)
    
    @staticmethod
    def close_db() -> bool:
        """
        Close the connection to the database. Wrapper of :meth:`DbManager.db.close`
        :return: True if the connection successfully closed, False otherwise
        :rtype: bool
        """
        return DbManager.db.close()

    @staticmethod
    def get_tables(schema=None) -> list:
        """
        Get the list of tables. Wrapper of :meth:`DbManager.db.get_tables`
        :return: The list of the tables
        :rtype: list
        """
        return DbManager.db.get_tables(schema)

# ####################################################################
#
# Model class
#
# ####################################################################
 
class Model(PWModel,Base):
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

    _kv_store: KVStore = None
    _uuid = None
    _uri_name = "model"
    _uri_delimiter = "$"

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

        self._uri_name = self.full_classname(slugify=True)
        self._init_store()

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database
        :return: The model
        :rtype: `Model` instance
        """
        type_str = slugify(self.type)
        mew_model_t = Controller.get_model_type(type_str)

        if type(self) == mew_model_t:
            return self
   
        # instanciate the class and shallow copy data
        model = mew_model_t()
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

    def __generate_uri(self) -> str:
        """ 
        Generates the uri of the model
        :return: The uri
        :rtype: str
        """
        return self._uri_name + Model._uri_delimiter + str(self.id)

    # -- H --

    # def has_data(self) -> bool:
    #     """
    #     Returns True if the `data` is not empty, False otherwise
    #     :return: True if the `data` is not empty, False otherwise
    #     :rtype: bool
    #     """
    #     return len(self.data) > 0

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
        return uri.split(cls._uri_delimiter)

    # -- S --

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

    @property
    def uri_name(self) -> str:
        """ 
        Returns the uri_name of the model
        :return: The uri_name
        :rtype: str
        """
        return self._uri_name

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
            except:
                transaction.rollback()
                return False

        return True

    # -- W --

    class Meta:
        database = DbManager.db
        table_function = format_table_name

# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):
    """
    Viewable class
    :property _view_model_specs: The list of registered view model types.
    :type specs: dict
    """

    _view_model_specs: dict = {}

    def as_json(self):
        """
        Returns JSON (a dictionnary) representation of the model
        :return: The JSON dictionary 
        :rtype: dict
        """
        return {
            "id" : self.id,
            "data" : self.data,
            "uri": self.uri,
            "creation_datetime" : self.creation_datetime,
        }

    def as_html(self):
        """
        Returns HTML representation of the model
        :return: The HTML text
        :rtype: str
        """
        return "<x-gws class='gws-model' id='{}' data-id='{}' data-uri='{}'></x-gws>".format(self._uuid, self.id, self.uri)

    def create_view_model_by_name(self, type_name: str):
        """
        Creates an instance of a registered view model type
        :param type_name: The slugified type name of the view model to create
        :type type_name: str
        :return: The created view model
        :rtype: ViewModel
        :raises Exception: If the view model cannot be created
        """
        if not isinstance(type_name, str):
            Logger.error(Exception(self.classname(), "create_view_model_by_name", "The view name must be a string"))
        
        view_model_t = self._view_model_specs.get(type_name,None)

        if isinstance(view_model_t, type):
            view_model = view_model_t(self)
            return view_model
        else:
            Logger.error(Exception(self.classname(), "create_view_model_by_name", "The view_model '"+view_model_type+"' is not found"))

    @classmethod
    def register_view_model_specs(cls, specs: list):
        """
        Registers a list of view model types
        :param specs: List of view model types
        :type specs: list
        """
        for t in specs:
            if not isinstance(t, type):
                Logger.error(Exception("Model", "register_specs", "Invalid spec. A {name, type} dictionnary or [type] list is expected, where type is must be a ViewModel type or sub-type"))
            cls._view_model_specs[t.full_classname(slugify=True)] = t


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

    def __init__(self, specs: dict = None, *args, **kwargs):
        super().__init__(specs, *args, **kwargs)

        if self.id is None:
            self.data = {
                "specs": {},
                "params": {}
            }
            
        if not specs is None:
            if not isinstance(specs, dict):
                Logger.error(Exception(self.classname(), "__init__", f"The specs must be a dictionnary"))
            
            #convert type to str
            for k in specs:
                if isinstance(specs[k]["type"], type):
                    specs[k]["type"] = specs[k]["type"].__name__
            
            self.set_specs( specs )

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

    # -- P 

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

from gws.prism.event import EventListener
class Process(Viewable):
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

    _input: Input
    _output: Output
    _table_name = 'process'

    _job: 'Job' = None  #ref to the current job

    def __init__(self, name: str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.id is None:
            self.hash = self.__create_hash()

            C = type(self)
            try:
                proc = C.get(C.hash == self.hash)
                self.id = proc.id
            except:
                self.save()
                proc = C.get(C.hash == self.hash)
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
    def config(self):
        return self.get_active_job().config

    def __check_hash(self):
        actual_hash = self.__create_hash()
        if self.hash and self.hash != actual_hash:
            Logger.error(Exception("Process", "__set_hash", "Invalid process hash. The code source of the current process has changed."))

    def __create_hash(self):
        type_str = slugify(self.type)
        model_t = Controller.get_model_type(type_str)
        source = inspect.getsource(model_t)
        hash_object = hashlib.sha256((self.type+source).encode())
        return hash_object.hexdigest()

    # -- G --

    def get_param(self, name: str) -> [str, int, float, bool]:
        """
        Returns the value of a parameter of the process config by its name.
        :return: The paremter value
        :rtype: [str, int, float, bool]
        """
        return self.config.get_param(name)

    # -- L --

    # -- I --

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
        Returns True if the process is ready (i.e. all its ports are ready or it has never been run before), False otherwise.
        :return: True if the process is ready, False otherwise.
        :rtype: bool
        """
        return  (not self.is_running or \
                not self.is_finished) and \
                self._input.is_ready 

    def in_port(self, name: str) -> InPort:
        """
        Returns the port of the input by its name
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
        Returns the context name of the process
        :return: The name
        :rtype: str
        """
        return self.data.get("name","")

    @name.setter
    def name(self, name: str) -> str:
        """ 
        Returns the context name of the process
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
            msg = "The process is not ready. Please ensure that the process receives valid input resources and has not already been run"
            Logger.error(Exception(self.classname(), "run", msg))

        job = self.get_active_job()
        if not job.save():
            msg = "Cannot save the job"
            Logger.error(Exception(msg))
        
        if self._event_listener.exists('start'):
            self._event_listener.call('start', self)

    def _run_after_task( self, *args, **kwargs ):

        if self._event_listener.exists('end'):
            self._event_listener.call('end', self)

        logger = Logger()
        if self.name:
            logger.info(f"Task of {self.full_classname()} '{self.name}' successfully finished!")
        else:
            logger.info(f"Task of {self.full_classname()} successfully finished!")

        self.is_running = False
        self.is_finished = True

        job = self.get_active_job()
        job.update_state()
        job.save()

        res = self.output.get_resources()
        for k in res:
            if not res[k] is None:
                res[k]._set_job(job)
                res[k].save()

        if not self._output.is_ready:
            return
            #Logger.error(Exception(self.classname(), "run", "The output was not set after the task ended."))
        
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
        Sets the resource of an input port by its name

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
# Project class
#
# ####################################################################

class Project(Model):

    name = CharField(index=True)
    organization = CharField(index=True)
    is_active =  BooleanField(default=False, index=True)

    _table_name = 'project'
    
    @property
    def description(self):
        return self.data.get("description","")

    @description.setter
    def description(self, text):
        self.data["description"] = text

    class Meta:
        indexes = (
            # create a unique on name,organization
            (('name', 'organization'), True),
        )
# ####################################################################
#
# User class
#
# ####################################################################

class User(Model, BaseUser):

    firstname = CharField(index=True)
    sirname = CharField(index=True)
    organization = CharField(index=True)
    email =  CharField(index=True)
    is_active =  BooleanField(default=False, index=True)

    _table_name = 'user'

    class Meta:
        indexes = (
            # create a unique on email,organization
            (('email', 'organization'), True),
        )

# ####################################################################
#
# Job class
#
# ####################################################################

class Job(Model):
    """
    Job class.

    :property process: The process of the job
    :type process: Process
    :property config: The config of the job's process
    :type config: Config
    :property user: The user
    :type user: User
    """

    process_id = IntegerField(index=True)   # store id ref as it may represent different classes
    config_id = IntegerField(index=True)    # store id ref as it may represent config classes
    is_running: bool = BooleanField(default=False, index=True)
    is_finished: bool = BooleanField(default=False, index=True)
    
    _process = None
    _config = None

    _table_name = 'job'

    def __init__(self, process: Process = None, config: Config = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.id is None:
            if not isinstance(config, Config):
                Logger.error(Exception("Job", "__init__", "The config must be an instance of Config"))
 
            if not isinstance(process, Process):
                Logger.error(Exception("Job", "__init__", "The process must be an instance of Process"))
            
            self._config = config
            self._process = process
            self.update_state()

    # -- I -- 

    # -- P --

    @property
    def process(self):
        if not self._process is None:
            return self._process

        if self.process_id:
            proc = Process.get(Process.id == self.process_id)
            self._process = proc.cast()
            return self._process
        else:
            return None

    @property
    def config(self):
        if not self._config is None:
            return self._config

        if self.config_id:
            config = Config.get(Config.id == self.config_id)
            self._config = config.cast()
            return self._config
        else:
            return None

    # -- S --

    def update_state(self):
        """ 
        Update the state of the job
        """

        self.is_running = self.process.is_running
        self.is_finished = self.process.is_finished

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
                            Logger.error(Exception("Job", "save", f"Cannot save the resource output {k} of the job"))

                return True
            except Exception as err:
                transaction.rollback()
                print(err)
                return False

    # -- T --

    def __track_input_uri(self):
        res = self.process.input.get_resources()
        for k in res:
            if res[k] is None:
                continue
            
            if not res[k].is_saved():
                Logger.error(Exception("Process", "__track_input_uri", "Cannot track input uri. Please save the input resource before."))

            self.data["inputs"] = {}    
            self.data["inputs"][k] = res[k].uri

# ####################################################################
#
# Experiment class
#
# ####################################################################

class Experiment(Model):
    
    job = ForeignKeyField(Job, backref="experiment")
    user = ForeignKeyField(User, backref="experiments")
    project = ForeignKeyField(Project, backref="experiments")

    _table_name = 'experiment'


# ####################################################################
#
# Protocol class
#
# ####################################################################

class Protocol(Process):
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

    #/!\ Write protocols in the 'process' table
    #_table_name = 'process'

    def __init__(self, name: str = None, processes: dict = None, connectors: list = None, \
                interfaces: dict = None, outerfaces: dict = None, \
                *args, **kwargs):
        super().__init__(name = name, *args, **kwargs)

        if not processes is None:
            if not isinstance(processes, dict):
                Logger.error(Exception("Protocol", "__init__", "A dictionnary of processes is expected"))
            
            for name in processes:
                proc = processes[name]
                proc.name = name    #set context name
                if not isinstance(proc, Process):
                    Logger.error(Exception("Protocol", "__init__", "The dictionnary of processes must contain instances of Process"))
            
            self._processes = processes

            if not connectors is None:
                if not isinstance(connectors, list):
                    Logger.error(Exception("Protocol", "__init__", "A list of connectors is expected"))

                for conn in connectors:
                    if not isinstance(conn, Connector):
                        Logger.error(Exception("Protocol", "__init__", "The list of connector must contain instances of Connectors"))
            
                self._connectors = connectors

        if not interfaces is None:
            input_specs = { }
            for k in interfaces:
                input_specs[k] = interfaces[k]._resource_type

            # print(input_specs)
            self.__set_input_specs(input_specs)
            self._interfaces = interfaces

        if not outerfaces is None:
            output_specs = { }
            for k in outerfaces:
                output_specs[k] = outerfaces[k]._resource_type

            # print(output_specs)
            self.__set_output_specs(output_specs)
            self._outerfaces = outerfaces

        self.__set_pre_start_event()
        self.__set_on_end_event()

    # -- A --

    def add_process(self, name: str, process: Process):
        """ 
        Adds a process to the protocol
        :param name: Unique name of the process
        :type name: str
        :param process: The process
        :type process: Process
        """
        if not isinstance(process, Process):
            Logger.error(Exception("Protocol", "add_process", "The process must be an instance of Process"))

        self._processes[name] = process

    def add_connector(self, connector: Connector):
        """ 
        Adds a connector to the protocol
        :param connector: The connector
        :type connector: Connector
        :Logger.error(Exception: It the processes of the connection do not belong to the protocol)
        """
        if not isinstance(connector, Connector):
            Logger.error(Exception("Protocol", "add_connector", "The connector must be an instance of Connector"))
        
        if  not connector.left_process in self._processes.values() or \
            not connector.right_process in self._processes.values():
            Logger.error(Exception("Protocol", "add_connector", "The connector processes must be belong to the protocol"))
        
        if connector in self._connectors:
            Logger.error(Exception("Protocol", "add_connector", "Duplciated connector"))

        self._connectors.append(connector)

    # -- B --

    def __build_from_settings(self, settings):
        pass
    
    # -- C --

    @classmethod
    def create_table(cls, *args, **kwargs):
        if not Experiment.table_exists():
            Experiment.create_table()
        
        if not Config.table_exists():
            Config.create_table()

        super().create_table(*args, **kwargs)

    def __create_settings( self ):
        settings = dict(
            nodes = {},
            links = []
        )
        
        for conn in self._connectors:
            link = conn.link
            for k in self._processes:
                if link["from"]["node"] is self._processes[k]:
                    link["from"]["node"] = k
                elif link["to"]["node"] is self._processes[k]:
                    link["to"]["node"] = k
        
        for k in self._processes:
            settings["nodes"][k] = self._processes.full_classname()

        #settings["interfaces"] = {}
        #settings["outerfaces"] = {}

        return settings

    # -- I --

    def is_child(self, process: Process) -> bool:
        """ 
        Returns True if the process is in the Protocol, False otherwise
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

    # -- R --
    
    async def run(self):
        """ 
        Runs the process and save its state in the database.
        Override mother class method.
        """
        self._run_before_task()

        # self.task()
        #--------- START BUILT-IN PROTOCOL TASK ---------

        sources = []
        for k in self._processes:
            proc = self._processes[k]
            if proc.is_ready or self.is_interfaced_with(proc):
                sources.append(proc)

        for proc in sources:
            await proc.run()

        #------------- END BUILT-IN PROTOCOL TASK ---------


    def _run_after_task(self, *args, **kwargs):
        self._set_outputs()
        e = Experiment(
            job = self.get_active_job(),
            user = Controller.get_test_user(),
            project = Controller.get_test_project()
        )
        e.save()
        super()._run_after_task()

    # -- S --

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
            if self.is_outerfaced_with(proc):
                sinks.append(proc)

        for proc in sinks:
            # proc.on_end( _set_outputs_and_propagate )
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
        
    @property
    def settings( self ):
        return self.__create_settings()

    @settings.setter
    def settings( self, settings: dict ):
        self.__build_from_settings( settings )

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
    _table_name = 'resource'

    def _set_job(self, job: 'Job'):
        """ 
        Sets the process of the resource
        :param process: The process
        :type process: Process
        """

        if not isinstance(job, Job):
            Logger.error(Exception("Resource", "_set_job", "The job must be an instance of Job."))

        self.job = job

# ####################################################################
#
# ViewModel class
#
# ####################################################################

class ViewModel(Model):
    """ 
    ViewModel class
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
    _table_name = 'view_model'

    def __init__(self, model_instance: Model = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if isinstance(model_instance, Model):
            self._model = model_instance
            self._model.register_view_model_specs( [type(self)] )

    # -- A --

    def as_json(self):
        """
        Returns JSON (a dictionnary) representation of the view mode
        :return: The JSON (dictionary)
        :rtype: dict
        """
        return {
            "id" : self.id,
            "data" : self.data,
            "uri": self.uri,
            "model": self.model.as_json(),
            "creation_datetime" : self.creation_datetime,
        }

    def as_html(self):
        """
        Returns HTML representation of the view model
        :return: The HTML text
        :rtype: str
        """
        return "<x-gws class='gws-model' id='{}' data-id='{}' data-uri='{}'></x-gws>".format(self._uuid, self.id, self.uri)

    # -- G --

    def get_view_uri(self, params: dict={}) -> str:
        """
        Returns the uri of the view (alias of the uri of the view model)
        :param params: The uri parameters
        :type params: dict
        :return: The uri
        :rtype: str
        """
        if len(params) == 0:
            params = ""
        else:
            params = urllib.parse.quote(str(params))
        return '/view/' + self.uri + '/' + params

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
            model_t.register_view_model_specs( [cls] )

    def render(self, params: dict = None) -> str:
        """
        Renders the view of the view model
        :param params: Rendering parameters
        :type params: dict
        :return: The rendering
        :rtype: str
        """
        if isinstance(params, dict):
            self.set_data(params)

        return self.template.render(self)
    
    # -- S --

    def set_template(self, template: ViewTemplate):
        """
        Sets the view template
        :param template: The view template
        :type template: ViewTemplate
        """
        if not isinstance(template, ViewTemplate):
            Logger.error(Exception(self.classname(),"set_template","The template must be an instance of ViewTemplate"))

        self.template = template
    
    def save(self, *args, **kwargs):
        """
        Saves the view model in database
        """
        if self._model is None:
            Logger.error(Exception(self.classname(),"save","This view_model has not model"))
        else:
            with DbManager.db.atomic() as transaction:
                try:
                    if self._model.save(*args, **kwargs):
                        self.model_id = self._model.id
                        self.model_type = self._model.full_classname()
                        return super().save(*args, **kwargs)
                    else:
                        Logger.error(Exception(self.classname(),"save","Cannot save the view_model. Please ensure that the model of the view_model is saved before"))
                except Exception as err:
                    transaction.rollback()
                    print(err)
                    return False

# ####################################################################
#
# Process ViewModel class
#
# ####################################################################

class ProcessViewModel(ViewModel):
    """ 
    ProcessViewModel class
    :property model: The model of the view model
    :type model: Process
    """

    _table_name = 'process_view_model'

    def __init__(self, model_instance=None, *args, **kwargs):
        super().__init__(model_instance=model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/model/process.html"), type="html")



# ####################################################################
#
# Resource ViewModel class
#
# ####################################################################

class ResourceViewModel(ViewModel):
    """ 
    ResourceViewModel class
    :property model: The model of the view model
    :type model: Resource
    """

    _table_name = 'resource_view_model'

    def __init__(self, model_instance=None, *args, **kwargs):
        super().__init__(model_instance=model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings.retrieve()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/model/resource.html"), type="html")


