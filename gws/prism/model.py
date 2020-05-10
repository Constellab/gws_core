#
# Python GWS model
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import asyncio
from datetime import datetime
from peewee import IntegerField, DateField, DateTimeField, CharField, ForeignKeyField, Model as PWModel
from peewee import SqliteDatabase
from playhouse.sqlite_ext import JSONField
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, JSONResponse, PlainTextResponse
import urllib.parse

from gws.settings import Settings
from gws.prism.base import Base
from gws.prism.controller import Controller
from gws.prism.view import ViewTemplate

class DbManager(Base):
    """
        GWS DbManager for managing backend sqlite databases. 
    """
    settings = Settings.retrieve()
    db = SqliteDatabase(settings.db_path)
    
    @staticmethod
    def create_tables(models, **options):
        DbManager.db.create_tables(models, **options)

    @staticmethod
    def drop_tables(models, **options):
        DbManager.db.drop_tables(models, **options)

    @staticmethod
    def connect_db() -> bool:
        return DbManager.db.connect(reuse_if_open=True)
    
    @staticmethod
    def close_db() -> bool:
        return DbManager.db.close()

    @staticmethod
    def get_tables(schema=None) -> list:
        return DbManager.db.get_tables(schema)

# ####################################################################
#
# Field class
#
# ####################################################################

class ModelProp(ForeignKeyField):
    def __init__(self, model, field=None, backref=None, on_delete=None, on_update=None, deferrable=None, _deferred=None, rel_model=None, to_field=None, object_id_name=None, lazy_load=True, related_name=None, *args, **kwargs):
        super().__init__(model, field=field, backref=backref, on_delete=on_delete, on_update=on_update, deferrable=deferrable, _deferred=_deferred, rel_model=rel_model, to_field=to_field, object_id_name=object_id_name, lazy_load=lazy_load, related_name=related_name, *args, **kwargs)

# ####################################################################
#
# Model class
#
# ####################################################################
 
class Model(PWModel,Base):
    """
        GWS Model class for storing data in databases. 
    """
    id = IntegerField(primary_key = True)
    data = JSONField(null = True, default={})
    creation_datetime = DateTimeField(default = datetime.now)
    registration_datetime = DateTimeField()
    
    __uri_name = "model"
    __uri_delimiter = "/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__uri_name = self.classname(slugify=True)     

        Controller.register_model_specs([type(self)])   
        Controller._register_model_instances([self])

    def clear_data(self, save: bool = False):
        self.data = None
        if save:
            self.save()
    
    
    def has_data(self) -> bool:
        return len(self.data) > 0

    def insert_data(self, kv: dict):
        if isinstance(kv,dict):
            for k in kv:
                self.data[k] = kv[k]
        else:
            raise Exception(self.classname(),"add_data","The data must be a dictionary")

    def is_registered(self) -> bool:
        return (self.registration_datetime is not None)

    @classmethod
    def parse_uri(cls, uri: str) -> list:
        return uri.split(cls.__uri_delimiter)

    
    @property
    def uri_id(self) -> str:
        return self.id

    @property
    def uri_name(self) -> str:
        return self.__uri_name

    @property
    def uri(self) -> str:
        if self.id is None:
            raise Exception(self.classname(), "uri", "No uri available. Please save the resource before")
        else:
            return self.__uri_name + Model.__uri_delimiter + str(self.id)

    def set_data(self, kv: dict):
        if isinstance(kv,dict):
            self.data = kv
        else:
            raise Exception(self.classname(),"set_data","The data must be a JSONable dictionary")  

    def save(self, *args, **kwargs) -> bool:
        if not self.table_exists():
            self.create_table()

        self.registration_datetime = datetime.now()
        return super().save(*args, **kwargs)
    
    def __eq__(self, other: 'Model') -> bool:
        """ 
            Comparison
        """
        if not isinstance(other, Model):
            return False

        return (self is other) or (self.id == other.id)

    class Meta:
        database = DbManager.db

# ####################################################################
#
# Viewable class
#
# ####################################################################
 
class Viewable(Model):
    view_model_specs: dict = {}

    def create_view_model_by_name(self, view_name: str):
        if not isinstance(view_name, str):
            raise Exception(self.classname(), "create_view_model_by_name", "The view name must be a string")
        
        view_model_type = self.view_model_specs.get(view_name,None)

        if isinstance(view_model_type, type):
            view_model = view_model_type(self)
            return view_model
        else:
            raise Exception(self.classname(), "create_view_model_by_name", "The view type is not valid")

    @classmethod
    def register_view_model_specs(cls, view_model_specs: list):
        for t in view_model_specs:
            if not isinstance(t, type):
                raise Exception("Model", "register_view_model_specs", "Invalid spec. A {name, type} dictionnary or [type] list is expected, where type is must be a ViewModel type or sub-type")
            cls.view_model_specs[t.name] = t

# ####################################################################
#
# Resource class
#
# ####################################################################

class Resource(Viewable):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# ####################################################################
#
# Port class
#
# ####################################################################

class Port(Base):
    _resource_type: Resource
    _resource: Resource
    _next: list = []
    _is_connected : bool = False
    _parent: 'IO'

    def __init__(self, parent: 'IO'):
        self._resource = None
        self._next = []
        self._is_connected = False
        self._parent = parent

    @property
    def resource(self) -> Resource:
        return self._resource
    
    def is_connnected(self) -> bool:
        return self._is_connected
    
    def is_ready(self)->bool:
        return isinstance(self._resource,Resource)

    def next_processes(self):
        next_proc = []
        for port in self._next:
            io = port._parent
            next_proc.append(io._parent)
        return next_proc

    def propagate(self):
        for port in self._next:
            port._resource = self._resource

    def set_resource(self, resource: Resource):
        if not isinstance(resource, Resource):
            raise Exception(self.classname(), "set_resource", "The resource must be an instance of Resource")

        self._resource = resource

    def __or__(self, other: 'Port'):
        """ 
            Connection operator
        """
        if not isinstance(other, Port):
            raise Exception(self.classname(), "|", "The port can only be connected to an instance of Port")

        if other.is_connnected():
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
    _ports: dict
    _parent: 'Process'

    def __init__(self, parent: 'Process'):
        self._parent = parent
        self._ports = dict()

    def __getitem__(self, name: str) -> Resource:
        if not isinstance(name, str):
            raise Exception(self.classname(), "__getitem__", "The port name must be a string")

        if self._ports.get(name, None) is None:
            raise Exception(self.classname(), "__getitem__", self.classname() +" port '"+name+"' not found")

        return self._ports[name].resource

    def __setitem__(self, name: str, resource: Resource):
        if not isinstance(name, str):
            raise Exception(self.classname(), "__setitem__", "The port name must be a string")

        if self._ports.get(name, None) is None:
            raise Exception(self.classname(), "__setitem__", self.classname() +" port '"+name+"' not found")
        
        if self._parent.is_started() or self._parent.is_finised():
            raise Exception(self.classname(), "__setitem__", "Cannot alter inputs/outputs of processes during or after running")

        self._ports[name].set_resource(resource)

    def create_port(self, name: str, resource_type: type):
        if not isinstance(name, str):
            raise Exception(self.classname(), "create_port", "Invalid port specs. The port name must be a string")

        if not isinstance(resource_type, type):
            raise Exception(self.classname(), "create_port", "Invalid port specs. The resource_type must be type. Maybe you provided an object instead of object type.")
        
        if not issubclass(resource_type, Resource):
            raise Exception(self.classname(), "create_port", "Invalid port specs. The resource_type must refer to subclass of Resource")
        
        if self._parent.is_started() or self._parent.is_finised():
            raise Exception(self.classname(), "__setitem__", "Cannot alter inputs/outputs of processes during or after running")

        port = Port(self)
        port._resource_type = resource_type
        self._ports[name] = port

    def is_ready(self)->bool:
        for k in self._ports:
            if not self._ports[k].is_ready():
                return False
        return True
    
    def get_port_names(self) -> list:
        return list(self._ports.keys)

    def next_processes(self) -> list:
        next_proc = []
        for k in self._ports:
            for proc in self._ports[k].next_processes():
                next_proc.append(proc)
        return next_proc

    @property
    def parent(self):
        return self._parent

# ####################################################################
#
# Input class
#
# ####################################################################

class Input(IO):
    pass

# ####################################################################
#
# Output class
#
# ####################################################################

class Output(IO):

    def propagate(self):
        for k in self._ports:
            self._ports[k].propagate()

# ####################################################################
#
# Process class
#
# ####################################################################

class Process(Viewable):
    input_specs: dict = {}
    output_specs: dict = {}

    _type = 'proc'
    _input: Input
    _output: Output

    _is_started : bool = False
    _is_finished : bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._input = Input(self)
        self._output = Output(self)
        self._is_started = False
        self._is_finished = False

        for k in self.input_specs:
            self._input.create_port(k,self.input_specs[k])

        for k in self.output_specs:
            self._output.create_port(k,self.output_specs[k])

    @property
    def input(self) -> 'Port':
        return self._input

    def is_started(self) -> bool:
        return self._is_started

    def is_finised(self) -> bool:
        return self._is_finished

    def is_ready(self) -> bool:
        return  (not self._is_started or \
                not self._is_finished) and \
                self._input.is_ready()

    def next_processes(self) -> list:
        return self._output.next_processes()

    async def run(self, params={}):
        if not isinstance(params, dict):
            raise Exception(self.classname(), "run", "The params must be a dictionnary")

        if not self.is_ready():
            raise Exception(self.classname(), "run", "The process is not ready. Please ensure that the process receives valid input resources and has not already been run")

        # save params in data attribute
        self.set_data(params)

        # run task
        await self.task(params)

        self._is_started = False
        self._is_finished = True

        if not self._output.is_ready():
            raise Exception(self.classname(), "run", "The output was not set after task end")
        
        self._output.propagate()

        for proc in self._output.next_processes():
            asyncio.create_task( proc.run(params) ) # schedule task be execute soon!
        
    @property
    def output(self) -> 'Port':
        return self._output

    async def task(self, params={}):
        """ 
            Process task
        """
        pass

    def set_input(self, name: str, resource: Resource):
        if not isinstance(name, str):
            raise Exception(self.classname(), "set_input", "The name must be a string")
        
        if not isinstance(resource, Resource):
            raise Exception(self.classname(), "set_input", "The resource must be an instance of Resource")

        self._input[name] = resource

    def iport(self, name: str) -> Port:
        """ 
            Operator iport(). Retrun input port by name
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), "<<", "The port name must be a string")

        return self._input._ports[name]

    def __lshift__(self, name: str) -> Port:
        """ 
            Operator <<(). Retrun input port by name
        """
        return self.iport(name)

    def oport(self, name: str) -> Port:
        """ 
            Operator oport(). Return output port by name
        """
        if not isinstance(name, str):
            raise Exception(self.classname(), ">>", "The port name must be a string")

        return self._output._ports[name]

    def __rshift__(self, name: str) -> Port:
        """ 
            Operator >>(). Return output port by name
        """
        return self.oport(name)

# ####################################################################
#
# View class
#
# ####################################################################

class ViewModel(Model):
    name: str = None
    template: ViewTemplate = ''
    model: 'Model' = ForeignKeyField(Model, backref='view_model')

    def __init__(self, model_instance: Model = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.name is None:
            raise Exception(self.classname(), "__init__", "No view name povided. It seems that you did set this property in the definition of the class")
  
        if not model_instance is None and not isinstance(model_instance, Model):
            raise Exception(self.classname(),"__init__","The model must be an instance af Model")
        elif isinstance(model_instance, Model):
            self.model = model_instance
            self.model.register_view_model_specs([ type(self) ])

    def get_update_view_uri(self, params={}) -> str:
        if len(params) == 0:
            params = ""
        else:
            params = urllib.parse.quote(str(params))
        return '/update_view/' + self.uri + '/' + params

    def get_create_view_uri(self, params={}) -> str:
        if len(params) == 0:
            params = ""
        else:
            params = urllib.parse.quote(str(params))
        return '/create_view/' + self.uri + '/' + params

    def render(self, params: dict = None) -> str:
        if isinstance(params, dict):
            self.set_data(params)

        return self.template.render(self)
    
    def set_template(self, template: ViewTemplate):
        if not isinstance(template, ViewTemplate):
            raise Exception(self.classname(),"__init__","The template must be an instance of ViewTemplate")

        self.template = template
    
    def save(self, *args, **kwargs):
        if self.model is None:
            raise Exception(self.classname(),"__init__","Failure while trying to save the model of the view_model. Please ensure that the model of the view_model's is saved before saving the view_model.")
        else:
            if self.model.save(*args, **kwargs):
                self.data["model_id"] = self.model.id
                return super().save(*args, **kwargs)
            else:
                raise Exception(self.classname(),"__init__","Failure while trying to save the model of the view_model. Please ensure that the model of the view_model's is saved before saving the view_model.")