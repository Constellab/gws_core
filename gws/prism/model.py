# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import asyncio
import uuid
from datetime import datetime
from peewee import Field, IntegerField, DateField, DateTimeField, CharField, BooleanField, ForeignKeyField, Model as PWModel
from peewee import SqliteDatabase
from playhouse.sqlite_ext import JSONField

from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, JSONResponse, PlainTextResponse
import urllib.parse

from gws.prism.base import slugify
from gws.settings import Settings
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
    :property type: The type of the model
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
        self._read_store()

        Controller.register_model_specs([type(self)])

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database
        :return: The model
        :rtype: `Model` instance
        """
        type_str = slugify(self.type)
        mew_model_t = Controller.model_specs[type_str]

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

    def has_data(self) -> bool:
        """
        Returns True if the `data` is not empty, False otherwise
        :return: True if the `data` is not empty, False otherwise
        :rtype: bool
        """
        return len(self.data) > 0

    # -- I --

    # def is_registered(self) -> bool:
    #     """
    #     Returns True if the model is registered to the controller, False otherwise
    #     :return: True if the model is registered to the controller, False otherwise
    #     :rtype: bool
    #     """
    #     return self.uuid in Controller.models

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

    # -- R --

    def _read_store(self):
        """ 
        Interface to implement. Allows to read huge model content from the store.

        Reads the model content from the store when creating the model. 
        This method is called by the constructor and must be implemented by 
        child classes if required
        """
        pass

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
        Returns the path of the store of the model
        :return: The path of the store
        :rtype: str
        """
        settings = Settings.retrieve()
        db_dir = settings.get("db_dir")
        return os.path.join(db_dir, self.uri)

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
            tf = self.save()
        
        self._write_store()

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

    def _write_store(self):
        """ 
        Interface to implement. Allows to write huge model content in the store.

        Writes the model content in the store when saving the model. This method is called by the 
        :meth:`save` and must be implemented by child classes to define if required 
        """
        pass

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
    :property view_model_specs: A dictionnary of registered view model types. Only 
    registered instance view models type can be created by the viewable.
    :type view_model_specs: dict
    """

    view_model_specs: dict = {}

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
        
        view_model_t = self.view_model_specs.get(type_name,None)

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
            cls.view_model_specs[t.full_classname(slugify=True)] = t

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
    _next: list = []
    _is_connected : bool = False
    _parent: 'IO'

    def __init__(self, parent: 'IO'):
        self._resource = None
        self._next = []
        self._is_connected = False
        self._parent = parent

    @property
    def resource(self) -> 'Resource':
        """
        Returns the resoruce of the port
        :return: The resource
        :rtype: Resource
        """
        return self._resource
    
    @property
    def is_connected(self) -> bool:
        """
        Returns True if the port is connected to a process, False otherwise
        :return: True if the port is connected, False otherwise.
        :rtype: bool
        """
        return self._is_connected
    
    @property
    def is_ready(self)->bool:
        """
        Returns True if the port is ready (i.e. contains a resource), False otherwise
        :return: True if the port is ready, False otherwise.
        :rtype: bool
        """
        return isinstance(self._resource, Resource)

    def next_processes(self):
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

        if other.is_connected:
            raise Exception(self.classname(), "|", "The right-hand side port is already connected")

        if self == other:
            raise Exception(self.classname(), "|", "Self connection not allowed")

        self._next.append(other)
        other._is_connected = True
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

    def next_processes(self) -> list:
        """ 
        Returns the list of (right-hand side) processes connected to the IO ports
        :return: List of processes
        :rtype: list
        """
        next_proc = []
        for k in self._ports:
            for proc in self._ports[k].next_processes():
                next_proc.append(proc)
        return next_proc

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
    Config class that represent the configuration of a process. A configuration is
    a collection of parameters
    """

    specs = {}
    _table_name = 'config'

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
        return self.data.get(name,default)

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

        self.data[name] = value

    class Meta:
        table_name = 'config'

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
    config_id = IntegerField(null=True, index=True)         #lazy FK reference
    is_running = BooleanField(default=False, index=True)
    is_finished = BooleanField(default=False, index=True)
    
    input_specs: dict = {}
    output_specs: dict = {}
    config_specs: dict = {}
    
    _on_start = None
    _on_end = None

    _config: Config
    _input: Input
    _output: Output
    _table_name = 'process'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._input = Input(self)
        self._output = Output(self)
        self._config = None

        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

        self.__retrieve_config()

    # -- C --

    @property
    def config(self) -> Config:
        """
        Returns the config of the process
        :return: The config
        :rtype: Config
        """
        return self._config

    # -- G --

    def get_param(self, name: str) -> [str, int, float, bool]:
        """
        Returns the value of a parameter of the process config by its name
        :return: The paremter value
        :rtype: [str, int, float, bool]
        """
        return self._config.get_param(name)

    # -- I --

    @property
    def input(self) -> 'Input':
        """
        Returns input of the process
        :return: The input
        :rtype: Input
        """
        return self._input

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the process is ready (i.e. all its ports are ready, it has never been run before), False otherwise
        :return: True if the process is ready, False otherwise.
        :rtype: bool
        """
        return  (not self.is_running or \
                not self.is_finished) and \
                self._input.is_ready and \
                not self._config is None

    def iport(self, name: str) -> Port:
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
        Alias of :meth:`iport`.

        Returns the port of the input by its name
        :return: The port
        :rtype: Port
        """
        return self.iport(name)

    # -- N --

    def next_processes(self) -> list:
        """ 
        Returns the list of (right-hand side) processes connected to the IO ports
        :return: List of processes
        :rtype: list
        """
        return self._output.next_processes()

    # -- O --

    @property
    def output(self) -> 'Output':
        """
        Returns output of the process
        :return: The output
        :rtype: Output
        """
        return self._output

    def oport(self, name: str) -> Port:
        """
        Returns the port of the output by its name
        :return: The port
        :rtype: Port
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), ">>", "The port name must be a string")

        return self._output._ports[name]

    # -- R -- 

    @classmethod
    def register_config_specs(cls, config_specs: list):
        """ 
        Register a list of config types. Only instances of registered config types can be
        used to configure the process
        :param config_specs: List of config types
        :type config_specs: list
        """
        for config_t in config_specs:
            if not isinstance(config_t, type):
                raise Exception("Process", "register_config_specs", "Invalid specs")
            cls.config_specs[config_t.full_classname(slugify=True)] = config_t

    async def run(self):
        """ 
        Runs the process and save its state in the database.
        """
        if not self.is_ready:
            raise Exception(self.classname(), "run", "The process is not ready. Please ensure that the process receives valid input resources and has not already been run")
 
        self.is_running = True

        # run task
        await self.task()

        self.is_running = False
        self.is_finished = True

        if not self._output.is_ready:
            raise Exception(self.classname(), "run", "The output was not set after task end")
        
        output_resources = self.output.get_resources()
        for k in output_resources:
            output_resources[k]._set_process(self)

        self.save()
        self._output.propagate()
        
        for proc in self._output.next_processes():
            asyncio.create_task( proc.run() )       # schedule task be executed soon!

    def __rshift__(self, name: str) -> Port:
        """ 
        Alias of :meth:`oport`.
        
        Returns the port of the output by its name
        :return: The port
        :rtype: Port
        """
        return self.oport(name)

    def __retrieve_config(self):
        """ 
        Retrieves the config of th eprocess from the database
        """
        try:
            self._config = Config.get_by_id(self.config_id)     #lazy reference
        except:
            config_t = None
            if 'default' in self.config_specs:
                config_t =  self.config_specs['default']
            else:
                if not bool(self.config_specs):
                    raise Exception("Process", "__retrieve_config", f"No default config defined for {type(self)}")
            
                config_t =  list(self.config_specs.values())[0]

            self._config = config_t()
            

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
            raise Exception(self.classname(), "set_input", "The name must be a string")
        
        if not isinstance(resource, Resource):
            raise Exception(self.classname(), "set_input", "The resource must be an instance of Resource")

        self._input[name] = resource

    def set_config(self, config: ['Config', dict]):
        """ 
        Sets the config of the process
        :param config: A config to assign
        :type config: [Config, dict]
        """
        if not bool(self.config_specs):
            raise Exception(self.classname(), "set_config", "The config_specs is empty")

        if isinstance(config, tuple(self.config_specs.values())):
            self._config = config
        elif isinstance(config, dict):
            if self._config is None:
                tab = list(self.config_specs.values())
                if len(tab) == 1:
                    self._config = tab[0]()
                else:
                    raise Exception(self.classname(), "set_config", "Cannot resolve the approriate Config to create. Please create the config before.")

            self._config.data = config
        else:
            raise Exception(self.classname(), "set_config", "The config must be a Config or a dictionnary")

    def set_param(self, name: str, value: [str, int, float, bool]):
        """ 
        Sets the value of a config parameter
        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """
        self._config.set_param(name, value)

    def save(self, *args, **kwargs):
        """ 
        Save the process in the database. 
        
        Also save the config, the input/output resources
        and the next processes.
        """
        with DbManager.db.atomic() as transaction:
            try:
                tf = True

                self.data["inputs"] = {}
                resources = self.input.get_resources()
                for k in resources:
                    if resources[k] is None:
                        continue
                    
                    tf = tf and resources[k].save(*args, **kwargs)
                    self.data["inputs"][k] = resources[k].uri

                self.__save_config()
                tf = tf and super().save(*args, **kwargs)
        
                resources = self.output.get_resources()
                for k in resources:
                    if resources[k] is None:
                        continue

                    if not resources[k].id is None:
                        tf = tf and resources[k].save(*args, **kwargs)

                for proc in self.next_processes():
                    tf = tf and proc.save(*args, **kwargs)

                if not tf:
                    raise Exception("Process", "save", "Cannot save process")

                return tf
            except Exception as err:
               transaction.rollback()
               print(err)
               return False

    def __save_config(self) -> bool:
        """ 
        Save the config in the database. 
        """
        if not self._config.save():
            raise Exception("Process", "__save_config", "Cannot save config")
        self.config_id = self._config.id

    # -- T --

    async def task(self, params={}):
        """ 
        Task interface.
        
        To be implemented in child classes
        """
        pass


    class Meta:
        table_name = 'process'

# class NullProcess(Process):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.id = 1
#         self._input = Input(self)
#         self._output = Output(self)
    
#     async def run(self, params={}):
#         raise Exception("NullProcess", "run", "NullProcess cannot be executed")
    
#     async def task(self, params={}):
#         raise Exception("NullProcess", "task", "NullProcess cannot cannot have a task")

#     class Meta:
#         table_name = 'null_process'

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

    process = ForeignKeyField(Process, null=True, backref='process')
    _table_name = 'resource'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.process:
            self.process = self.process.cast()

    def _set_process(self, process: 'Process'):
        """ 
        Sets the process of the resource
        :param process: The process
        :type process: Process
        """
        self.process = process
    
    class Meta:
        table_name = 'resource'

# class NullResource(Resource):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.id = 1
#         self.process = NullProcess()
    
#     def _set_process(self, process: 'Process'):
#         raise Exception("NullResource", "_set_process", "NullResource is related to a NullProcess")

#     def save(self, *args, **kwargs):
#         if self.id is None:
#             self.id = 1
#         return self.save(*args, **kwargs)

#     class Meta:
#         table_name = 'null_resource'

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

    model: 'Model' = ForeignKeyField(Model, backref='view_model')
    template: ViewTemplate = None
    _table_name = 'view_model'

    def __init__(self, model_instance: Model = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        is_invalid_model_instance = not model_instance is None and \
                                    not isinstance(model_instance, Model)
        if is_invalid_model_instance:
            raise Exception(self.classname(),"__init__","The model must be an instance of Model")
        elif isinstance(model_instance, Model):
            self.model = model_instance
            self.model.register_view_model_specs([ type(self) ])
        else:
            self.model = self.model.cast()

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
        if self.model is None:
            raise Exception(self.classname(),"save","This view_model has not model")
        else:
            with DbManager.db.atomic() as transaction:
                try:
                    if self.model.save(*args, **kwargs):
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

    model: 'Process' = ForeignKeyField(Process, backref='view_model')
    _table_name = 'process_view_model'

    def __init__(self, model_instance=None, *args, **kwargs):

        is_invalid_model_instance = not model_instance is None and \
                                    not isinstance(model_instance, Process)
        if is_invalid_model_instance:
            raise Exception("ProcessViewModel", "__init__", "The model must be an instance af Process")

        super().__init__(model_instance=model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/model/process.html"), type="html")

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

    model: 'Resource' = ForeignKeyField(Resource, backref='view_model')
    _table_name = 'resource_view_model'

    def __init__(self, model_instance=None, *args, **kwargs):

        is_invalid_model_instance = not model_instance is None and \
                                    not isinstance(model_instance, Resource)
        if is_invalid_model_instance:
            raise Exception("ResourceViewModel", "__init__", "The model must be an instance af Process")

        super().__init__(model_instance=model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings.retrieve()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/model/resource.html"), type="html")

    class Meta:
        table_name = 'resource_view_model'