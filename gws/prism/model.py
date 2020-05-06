#
# Python GWS model
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import asyncio
import uuid
from datetime import datetime
from peewee import IntegerField, DateField, DateTimeField, Model as PwModel
from peewee import SqliteDatabase
from playhouse.sqlite_ext import JSONField
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, JSONResponse, PlainTextResponse


from gws import settings
from gws.prism.base import Base
from gws.prism.controller import Controller

class DbManager(Base):
    """
        GWS DbManager for managing backend sqlite databases. 
    """
    db = SqliteDatabase(settings.db_path)
    
    @staticmethod
    def connect_db():
        DbManager.db.connect(reuse_if_open=True)
    
    @staticmethod
    def close_db():
        DbManager.db.close()

# ####################################################################
#
# Model class
#
# ####################################################################
 
class Model(PwModel,Base):
    """
        GWS Model class for storing data in databases. 
    """
    id = IntegerField(primary_key = True)
    data = JSONField(null = True)
    creation_datetime = DateTimeField(default = datetime.now)
    registration_datetime = DateTimeField()

    #_view_instances: dict
    view_types: dict
    _uuid: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creation_datetime = datetime.now()
        self._uuid = str(uuid.uuid4())

    def clear_data(self, save: bool = False):
        self.data = None
        if save:
            self.save()
    
    def create_view_instance(self, view_name: str):
        if not isinstance(view_name, str):
            raise Exception(self.classname(), "create_view_instance", "The view name must be a string")
        
        view_class = self.view_types.get(view_name,None)
        if not isinstance(view_class, type):
            raise Exception(self.classname(), "create_view_instance", "The view type is not valid")
        
        view = view_class(self)
        return view

    def has_data(self) -> bool:
        return len(self.data) > 0

    def insert_data(self, kv: dict):
        if isinstance(kv,dict):
            for k, v in kv.items():
                self.data[k] = v
        else:
            raise Exception(self.classname(),"add_data","The data must be a dictionary")

    def is_registered(self) -> bool:
        return (self.registration_datetime is not None)

    @property
    def uri(self) -> str:
        return '/' + self.classname(slugify=True) + '/' + self._uuid

    @property
    def uuid(self) -> str:
        return self._uuid

    def set_data(self, kv: dict):
        if isinstance(kv,dict):
            self.data = kv
        else:
            raise Exception(self.classname(),"set_data","The data must be a JSONable dictionary")  

    def save(self, *args, **kwargs):
        self.registration_datetime = datetime.now()
        return super().save(*args, **kwargs)
    
    def __eq__(self, other: 'Model') -> bool:
        """ 
            Comparison
        """
        if not isinstance(other, Model):
            return False

        return self._uuid == other._uuid

    class Meta:
        database = DbManager.db

# ####################################################################
#
# Resource class
#
# ####################################################################

class Resource(Model):
    
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
        #self._resource_type = resource_type
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

class Process(Model):
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
        self.set_params(params)

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

    @property
    def params(self) -> dict:
        return self.data['__params__']

    async def task(self, params={}):
        """ 
            Process task
        """
        pass
    
    def set_params(self, params: dict):
        if self.data is None:
            self.data = {}
        self.data['__params__'] = params

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

    # def __lt__(self, name: str) -> Resource:
    #     """ 
    #         Operator <(). Retrun input's port resource by name
    #     """
    #     if not isinstance(name, str):
    #         raise Exception(self.classname(), "<", "The port name must be a string")

    #     return self._input._ports[name].resource

    # def __gt__(self, name: str) -> Resource:
    #     """ 
    #         Operator >(). Retrun output's port resource by name
    #     """
    #     if not isinstance(name, str):
    #         raise Exception(self.classname(), ">", "The port name must be a string")

    #     return self._output._ports[name].resource


# ####################################################################
#
# ViewModel class
#
# ####################################################################

class ViewModel(Model):
    view: 'View'

    def __init__(self, view: 'View' = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}

        if not view is None:
            self.view = view
            meta = {
                "view_class" : view.classname(),
                "model_id" : view.model.id
            }
            self.data["__meta__"] = meta
            self.set_params({})
        else:
            meta = {
                "view_class" : "",
                "model_id" : ""
            }
            self.data["__meta__"] = meta
            self.set_params({})

    @property
    def params(self) -> dict:
        return self.data["params"]

    def set_params(self, params: dict):
        if not isinstance(params, dict):
            raise Exception(self.classname(), "set_params", "The params must be a dictionnary")
        self.data["params"] = params

    def save(self, *args, **kwargs):
        if self.view.model.id is None:
            raise Exception(self.classname(), "save", "Please save the Model of the view before saving the ViewModel")
        
        meta = {
            "view_class" : self.view.classname(),
            "model_id" : self.view.model.id
        }
        self.data["__meta__"] = meta
        return super().save(*args, **kwargs)
