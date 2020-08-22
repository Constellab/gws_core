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

from gws.logger import Logger
from gws.settings import Settings
from gws.store import KVStore
from gws.prism.base import slugify
from gws.prism.base import Base
from gws.prism.controller import Controller
from gws.prism.view import ViewTemplate, ViewTemplateFile

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
    #     return bool(self.data)

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
        :raise Exception: If no model is found
        """
        cursor = DbManager.db.execute_sql(f'SELECT type FROM {self._table_name} WHERE id = ?', str(id))
        row = cursor.fetchone()
        if len(row) == 0:
            raise Exception("Model", "fetch_type_by_id", "The model is not found.")
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
            raise Exception(self.classname(),"set_data","The data must be a JSONable dictionary")  
    
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
                    #model_list = Controller.models.values()
                
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
        table_name = 'model'

# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):
    """
    Viewable class
    :property default_view_models: The default list of registered view model types.
    :type specs: dict
    """

    default_view_models = []
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
            raise Exception(self.classname(), "create_view_model_by_name", "The view name must be a string")
        
        view_model_t = self._view_model_specs.get(type_name,None)

        if isinstance(view_model_t, type):
            view_model = view_model_t(self)
            return view_model
        else:
            raise Exception(self.classname(), "create_view_model_by_name", "The view_model '"+view_model_type+"' is not found")

    @classmethod
    def register_view_model_specs(cls, specs: list):
        """
        Registers a list of view model types
        :param specs: List of view model types
        :type specs: list
        """
        for t in specs:
            if not isinstance(t, type):
                raise Exception("Model", "register_specs", "Invalid spec. A {name, type} dictionnary or [type] list is expected, where type is must be a ViewModel type or sub-type")
            cls._view_model_specs[t.full_classname(slugify=True)] = t

# ####################################################################
#
# Port class
#
# ####################################################################

class Port(Base):
    """
    Port class. A port contains a resource and allows connecting processes.

    Example: [Left Process]-<output port> ---> <input port>-[Right Process]. 
    """

    _resource_type: 'Resource'
    _resource: 'Resource'
    _prev: 'Port' = None
    _next: list = []
    _is_left_connected : bool = False
    _parent: 'IO'

    def __init__(self, parent: 'IO'):
        self._resource = None
        self._next = []
        self._is_left_connected = False
        self._parent = parent
        self._resource_type = Resource

    @property
    def resource(self) -> 'Resource':
        """
        Returns the resoruce of the port
        :return: The resource
        :rtype: Resource
        """
        return self._resource
    
    @property
    def is_left_connected(self) -> bool:
        """
        Returns True if the port is left-connected to a another port
        :return: True if the port is left-connected, False otherwise.
        :rtype: bool
        """
        return not self._prev is None
    
    def is_left_connected_to(self, port: 'Port') -> bool:
        """
        Returns True if the port is left-connected to a given Port, False otherwise
        :return: True if the port is connected, False otherwise.
        :rtype: bool
        """
        return self._prev is port

    @property
    def is_right_connected(self) -> bool:
        """
        Returns True if the port is right-connected to a another port
        :return: True if the port is right-connected, False otherwise.
        :rtype: bool
        """
        return len(self._next) > 0

    def is_right_connected_to(self, port: 'Port') -> bool:
        """
        Returns True if the port is right-connected to a given Port, False otherwise
        :return: True if the port is connected, False otherwise.
        :rtype: bool
        """
        return port in self._next

    @property
    def is_ready(self)->bool:
        """
        Returns True if the port is ready (i.e. contains a resource), False otherwise
        :return: True if the port is ready, False otherwise.
        :rtype: bool
        """
        return isinstance(self._resource, self._resource_type) and self._resource.is_saved()

    def get_next_procs(self):
        """
        Returns the list of right-hand side processes connected to the port
        :return: List of processes
        :rtype: list
        """
        next_proc = []
        for port in self._next:
            io = port._parent
            next_proc.append(io._parent)
        return next_proc

    def propagate(self):
        """
        Propagates the resource of the port to the connected (right-hande side) port
        """
        for port in self._next:
            port._resource = self._resource

    def set_resource(self, resource: 'Resource'):
        """
        Sets the resource of the port
        :param resource: The input resource
        :type resource: Resource
        :raise Exception: If reource is not compatible with port
        """
        if not isinstance(resource, Resource):
            raise Exception(self.classname(), "set_resource", "The resource must be an instance of Resource")

        self._resource = resource

    def __or__(self, other: 'Port'):
        """ 
        Connection operator.

        Connect the port to another (right-hand side) port.
        :return: The right-hand sode port
        :rtype: Port
        :raise Exception: If the connection is not possible
        """
        if not isinstance(other, Port):
            raise Exception(self.classname(), "|", "The port can only be connected to an instance of Port")

        if other.is_left_connected:
            raise Exception(self.classname(), "|", "The right-hand side port is already connected")

        if self == other:
            raise Exception(self.classname(), "|", "Self connection not allowed")

        self._next.append(other)
        other._prev = self
        return other

# ####################################################################
#
# IO class
#
# ####################################################################

class IO(Base):
    """
    Base IO class. The IO class defines base functionalitie for the 
    Input and Output classes. A IO is a set of ports.
    """

    _ports: dict = {}
    _parent: 'Process'

    def __init__(self, parent: 'Process'):
        self._parent = parent
        self._ports = dict()

    # -- C --

    def create_port(self, name: str, resource_type: type):
        """ 
        Creates a port
        :param name: Name of the port
        :type name: str
        :param resource_type: The expected type of the resoruce of the port
        :type resource_type: type
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), "create_port", "Invalid port specs. The port name must be a string")

        if not isinstance(resource_type, type):
            raise Exception(self.classname(), "create_port", "Invalid port specs. The resource_type must be type. Maybe you provided an object instead of object type.")
        
        if not issubclass(resource_type, Resource):
            raise Exception(self.classname(), "create_port", "Invalid port specs. The resource_type must refer to subclass of Resource")
        
        if self._parent.is_running or self._parent.is_finished:
            raise Exception(self.classname(), "__setitem__", "Cannot alter inputs/outputs of processes during or after running")

        port = Port(self)
        port._resource_type = resource_type
        self._ports[name] = port

    # -- G --

    def __getitem__(self, name: str) -> 'Resource':
        """ 
        Bracket (getter) operator. Gets the content of a port by its name
        :param name: Name of the port
        :type name: str
        :return: The resource of the port
        :rtype: Resource
        :raise Exception: If the port is not found
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), "__getitem__", "The port name must be a string")

        if self._ports.get(name, None) is None:
            raise Exception(self.classname(), "__getitem__", self.classname() +" port '"+name+"' not found")

        return self._ports[name].resource

    def get_port_names(self) -> list:
        """ 
        Returns the names of all the ports
        :return: List of names
        :rtype: list
        """
        return list(self._ports.keys)

    def get_resources(self) -> dict:
        """ 
        Returns the resources of all the ports
        :return: List of resources
        :rtype: list
        """
        resources = {}
        for k in self._ports:
            resources[k] = self._ports[k].resource
        return resources

    # -- I --

    @property
    def is_ready(self)->bool:
        """
        Returns True if the IO is ready (i.e. all its ports are ready), False otherwise
        :return: True if the IO is ready, False otherwise.
        :rtype: bool
        """
        for k in self._ports:
            if not self._ports[k].is_ready:
                return False
        return True

    # -- N --

    def get_next_procs(self) -> list:
        """ 
        Returns the list of (right-hand side) processes connected to the IO ports
        :return: List of processes
        :rtype: list
        """
        next_proc = []
        for k in self._ports:
            for proc in self._ports[k].get_next_procs():
                next_proc.append(proc)
        return next_proc

    # -- P --

    @property
    def ports(self) -> dict:
        """ 
        Returns the list of ports
        :return: List of port
        :rtype: list
        """
        return self._ports

    @property
    def parent(self) -> 'Process':
        """ 
        Returns the parent of the IO, i.e. the process that holds this IO
        :return: The parent process
        :rtype: Process
        """
        return self._parent

    # -- S --

    def __setitem__(self, name: str, resource: 'Resource'):
        """ 
        Bracket (setter) operator. Sets the content of a port by its name
        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        :raise Exception: If the port is not found
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), "__setitem__", "The port name must be a string")

        if self._ports.get(name, None) is None:
            raise Exception(self.classname(), "__setitem__", self.classname() +" port '"+name+"' not found")

        self._ports[name].set_resource(resource)
    

# ####################################################################
#
# Input class
#
# ####################################################################

class Input(IO):
    """
    Input class
    """

    def __setitem__(self, name: str, resource: 'Resource'):
        """ 
        Bracket (setter) operator. Sets the content of a port by its name
        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        :raise Exception: If the port is not found
        """
        if self._parent.is_running or self._parent.is_finished:
            raise Exception(self.classname(), "__setitem__", "Cannot alter inputs of processes during or after running")

        super().__setitem__(name,resource)

# ####################################################################
#
# Output class
#
# ####################################################################

class Output(IO):
    """
    Output class
    """

    def links(self):
        proc = self._parent
        links = []
        for o_name in self.ports:
            o_port = self.ports[o_name]
            
            for next_proc in self.get_next_procs():
                for i_name in next_proc.input.ports:
                    i_port = next_proc.input.ports[i_name]
                    
                    if o_port.is_right_connected_to(i_port):
                        links.append(
                            {
                                "from": {"node": proc,  "port": o_name},
                                "to": {"node": next_proc,  "port": i_name}
                            }
                        )
        return links

    def propagate(self):
        """
        Propagates the resources of the child port sto the connected (right-hande side) ports
        """
        for k in self._ports:
            self._ports[k].propagate()

    def __setitem__(self, name: str, resource: 'Resource'):
        """ 
        Bracket (setter) operator. Sets the content of a port by its name
        :param name: Name of the port
        :type name: str
        :param resource: The input resource
        :type resource: Resource
        :raise Exception: If the port is not found
        """
        if not self._parent.is_running or self._parent.is_finished:
            raise Exception(self.classname(), "__setitem__", "Cannot alter outputs of processes during that is not started or after running")

        super().__setitem__(name,resource)
        
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
            raise Exception(self.classname(), "get_param", f"Parameter {name} does not exist'")
        
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
            raise Exception(self.classname(), "set_param", f"Parameter '{name}' does not exist.")
        
        param_t = self.specs[name]["type"]

        try:
            validator = Validator.from_type(param_t)
            value = validator.validate(value)
        except Exception as err:
            raise Exception(self.classname(), "set_param", f"Invalid parameter value '{name}'. Error message: {err}")

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
        :raise Exception: If the config is already saved
        """
        if not isinstance(specs, dict):
            raise Exception(self.classname(), "set_specs", f"The specs must be a dictionary.")
        
        if not self.id is None:
            raise Exception(self.classname(), "set_specs", f"Cannot alter the specs of a saved config")
        
        self.data = {
            "specs" : specs,
            "params" : {}
        }

    class Meta:
        table_name = 'config'

# # ####################################################################
# #
# # ProcessConfig class
# #
# # ####################################################################

# class ProcessConfig(Config):
#     """
#     ProcessConfig class.
#     """

#     _table_name = 'process_config'

#     class Meta:
#         table_name = 'process_config'

# ####################################################################
#
# Process class
#
# ####################################################################

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

    _on_start = None
    _on_end = None

    
    _input: Input
    _output: Output
    _table_name = 'process'

    _on_start = None
    _on_end = None

    _job: 'Job' = None  #ref to the current job

    def __init__(self, *args, **kwargs):
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

        self._input = Input(self)
        self._output = Output(self)

        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

    @property
    def config(self):
        return self.get_active_job().config
        
    # -- C --

    def __check_hash(self):
        actual_hash = self.__create_hash()
        if self.hash and self.hash != actual_hash:
            raise Exception("Process", "__set_hash", "Invalid process hash. The code source of the current process has changed.")

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

    def get_input_port(self, name: str) -> Port:
        """
        Returns the port of the input by its name
        :return: The port
        :rtype: Port
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), "<<", "The port name must be a string")

        return self._input._ports[name]

    # -- L --

    def __lshift__(self, name: str) -> Port:
        """
        Alias of :meth:`get_input_port`.

        Returns the port of the input by its name
        :return: The port
        :rtype: Port
        """
        return self.get_input_port(name)

    # -- N --

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

    def get_output_port(self, name: str) -> Port:
        """
        Returns the port of the output by its name.
        :return: The port
        :rtype: Port
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), ">>", "The port name must be a string")

        return self._output._ports[name]

    @property
    def on_end(self):
        return self._on_end

    @on_end.setter
    def on_end(self, callback):
        """
        Sets the function the execute after the process ends running. 
        :param callback: The function to execute
        :callback: `function`
        """
        if not hasattr(callback, '__call__'):
            raise Exception("Process", "on_start", "The callback function is not callable")
        self._on_end = callback

    @property
    def on_start(self):
        return self._on_start

    @on_start.setter
    def on_start(self, callback):
        """
        Sets the function the execute before running the process. 
        :param callback: The function to execute
        :callback: `function`
        """
        if not hasattr(callback, '__call__'):
            raise Exception("Process", "on_start", "The callback function is not callable")
        self._on_start = callback

    # -- R -- 

    async def run(self):
        """ 
        Runs the process and save its state in the database.
        """
        if not self.is_ready:
            raise Exception(self.classname(), "run", "The process is not ready. Please ensure that the process receives valid input resources and has not already been run")

        self.is_running = True

        # run task
        logger = Logger()
        logger.info(f"Running task {self.classname()} ...")

        if not self._on_start is None:
            await self._on_start( self )
        
        e = self.get_active_job()
        if not e.save():
            raise Exception("Process", "run", "Cannot save the job")

        await self.task()

        if not self._on_end is None:
            await self._on_end( self )

        logger.info(f"Task successfully finished!")

        self.is_running = False
        self.is_finished = True
        e.update_state()
        e.save()

        res = self.output.get_resources()
        for k in res:
            res[k]._set_job(e)
            res[k].save()

        if not self._output.is_ready:
            raise Exception(self.classname(), "run", "The output was not set after the task ended.")
       
        self._output.propagate()
        
        for proc in self._output.get_next_procs():
            asyncio.create_task( proc.run() )       # schedule task will be executed as soon as possible!

    def __rshift__(self, name: str) -> Port:
        """ 
        Alias of :meth:`get_output_port`.
        
        Returns the port of the output by its name
        :return: The port
        :rtype: Port
        """
        return self.get_output_port(name)     
        
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
            raise Exception(self.classname(), "set_input", "The name must be a string.")
        
        if not isinstance(resource, Resource):
            raise Exception(self.classname(), "set_input", "The resource must be an instance of Resource.")

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
            raise Exception(self.classname(), "set_config", "The config must be an instance of Config.")

    def set_param(self, name: str, value: [str, int, float, bool]):
        """ 
        Sets the value of a config parameter.
        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """
        self.config.set_param(name, value)

    async def task(self):
        """ 
        Task interface.
        To be implemented in child classes.
        """
        pass

    class Meta:
        table_name = 'process'

# ####################################################################
#
# Project class
#
# ####################################################################

class Project(Model):
    
    name: CharField(index=True, unique=True)

    _table_name = 'project'

    class Meta:
        table_name = 'project'

# ####################################################################
#
# User class
#
# ####################################################################

class User(Model):
    firstname: CharField(index=True)
    sirname: CharField(index=True)
    email: CharField(index=True, unique=True)

    _table_name = 'user'

    class Meta:
        table_name = 'user'

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
            if isinstance(config, Config):
                #self.config_id = config.id
                self._config = config
            
            if isinstance(process, Process):
                #self.process_id = process.id
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
    # def set_config(self, config: Config):
    #     self.config = config

    # def set_process(self, process: Process):
    #     self.process = process
    #     self.update_state()

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
                    raise Exception("Job", "save", "Cannot save the job. The process is not saved.")
                
                if not self.config.save():
                    raise Exception("Job", "save", "Cannot save the job. The config cannnot be saved.")
                
                self.process_id = self._process.id
                self.config_id = self._config.id

                self.__track_input_uri()
                if not super().save(*args, **kwargs):
                    raise Exception("Job", "save", "Cannot save the job.")
                
                res = self.process.output.get_resources()
                for k in res:
                    if res[k] is None:
                        continue

                    if not res[k].is_saved():
                        if not res[k].save(*args, **kwargs):
                            raise Exception("Job", "save", f"Cannot save the resource output {k} of the job")

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
                raise Exception("Process", "__track_input_uri", "Cannot track input uri. Please save the input resource before.")

            self.data["inputs"] = {}    
            self.data["inputs"][k] = res[k].uri

    class Meta:
        table_name = 'job'

# # ####################################################################
# #
# # ProtocolConfig class
# #
# # ####################################################################

# class ProtocolConfig(ProcessConfig):
#     """
#     ProtocolConfig class
#     """

#     _table_name = 'protocol_config'

#     class Meta:
#         table_name = 'protocol_config'

# ####################################################################
#
# Protocol class
#
# ####################################################################

class Protocol(Model):

    #config = ForeignKeyField(ProtocolConfig, null=True, backref='config')

    _procs: dict = {}
    _table_name = 'protocol'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #if not self.config:
        #    self.config = ProtocolConfig(specs = self.config_specs)
        #self.config = None

        self._procs = {}

    # -- A --

    def add(self, procs: dict):
        """ 
        Adds a dictionary of processes to the protocol
        :param procs: Dictionnary of processes. Keys are process names and Values are process instances.
        :type procs: dict
        """
        for k in procs:
            if not isinstance(procs[k], Process):
                raise Exception("Protocol", "add", "The process must be an instance of Process")
            self._procs[k] = procs[k]

    # -- B --

    def __build_from_settings(self, settings):
        pass
    
    # -- C --

    def __create_settings( self ):
        settings = dict(
            nodes = {},
            links = []
        )
        
        for k in self._procs:
            links = self._procs[k].output.links()
            for link in links:
                for name in self._procs:
                    if link["from"]["node"] is self._procs[name]:
                        link["from"]["node"] = name 
                        
                    if link["to"]["node"] is self._procs[name]:
                        link["to"]["node"] = name 

                settings["links"].append(links)

        for k in self._procs:
            settings["nodes"][k] = self._procs[k].full_classname()

        return settings

    # -- R --

    def remove(self, name: dict):
        """ 
        Remove a process from the protocol
        :param name: Name of the process to remove
        :type name: str
        """
        if name in self._procs:
            del self._procs[name]

    def realize(self):
        pass

    # -- S --

    @property
    def settings( self ):
        return self.__create_settings()

    @settings.setter
    def settings( self, settings: dict ):
        self.__build_from_settings( settings )

    class Meta:
        table_name = 'protocol'


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
            raise Exception("Resource", "_set_job", "The job must be an instance of Job.")

        self.job = job
    
    class Meta:
        table_name = 'resource'

# ####################################################################
#
# ViewModel class
#
# ####################################################################

class ViewModel(Model):
    """ 
    ViewModel class
    :property model: Model of the view model
    :type model: Model
    :property template: The view template
    :type template: ViewTemplate
    """

    #model: 'Model' = ForeignKeyField(Model, backref='view_models')
    model_id: int = IntegerField(index=True)
    model_type :str = CharField(index=True)
    _model = None
    template: ViewTemplate = None
    _table_name = 'view_model'

    def __init__(self, model_instance: Model = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # is_invalid_model_instance = not model_instance is None and \
        #                             not isinstance(model_instance, Model)
        # if is_invalid_model_instance:
        #     raise Exception(self.classname(),"__init__","The model must be an instance of Model")
        # elif isinstance(model_instance, Model):
        #     self.model = model_instance
        #     self.model.register_view_model_specs([ type(self) ])
        # else:
        #     self.model = self.model.cast()

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
            raise Exception(self.classname(),"set_template","The template must be an instance of ViewTemplate")

        self.template = template
    
    def save(self, *args, **kwargs):
        """
        Saves the view model in database
        """
        if self._model is None:
            raise Exception(self.classname(),"save","This view_model has not model")
        else:
            with DbManager.db.atomic() as transaction:
                try:
                    if self._model.save(*args, **kwargs):
                        self.model_id = self._model.id
                        self.model_type = self._model.full_classname()
                        return super().save(*args, **kwargs)
                    else:
                        raise Exception(self.classname(),"save","Cannot save the view_model. Please ensure that the model of the view_model is saved before")
                except Exception as err:
                    transaction.rollback()
                    print(err)
                    return False

    class Meta:
        table_name = 'view_model'

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

    #model: 'Process' = ForeignKeyField(Process, backref='view_models')
    _table_name = 'process_view_model'

    def __init__(self, model_instance=None, *args, **kwargs):

        # is_invalid_model_instance = not model_instance is None and \
        #                             not isinstance(model_instance, Process)
        # if is_invalid_model_instance:
        #     raise Exception("ProcessViewModel", "__init__", f"The model must be an instance af Process. Actual class is {type(model_instance)}")

        super().__init__(model_instance=model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/model/process.html"), type="html")

        # force all ProcessViewModel in the same table 
        cls = type(self)
        cls._table_name = 'resource_view_model'

    class Meta:
        table_name = 'process_view_model'

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

    #model: 'Resource' = ForeignKeyField(Resource, backref='view_models')
    _table_name = 'resource_view_model'

    def __init__(self, model_instance=None, *args, **kwargs):

        # is_invalid_model_instance = not model_instance is None and \
        #                             not isinstance(model_instance, Resource)
        # if is_invalid_model_instance:
        #     raise Exception("ResourceViewModel", "__init__", f"The model must be an instance af Process. Actual class is {type(model_instance)}")

        super().__init__(model_instance=model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings.retrieve()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/model/resource.html"), type="html")
        
        # force all ResourceViewModel in the same table 
        cls = type(self)
        cls._table_name = 'resource_view_model'

    class Meta:
        table_name = 'resource_view_model'
