# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from .process import Process
from .resource import Resource

class Source(Process):
    """
    Source process. 
    
    A source process is used to load and transfer a resource. No more action is done.
    """
    
    input_specs = {}
    output_specs = {'resource' : (Resource, )}
    config_specs = {
        'resource_uri': {"type": str, "default": None, 'description': "The uri of the resource"},
        'resource_type': {"type": str, "default": None, 'description': "The type of the resource"},
    }
    
    _is_plug = True
    
    async def task(self):
        from .service.model_service import ModelService
        r_uri = self.get_param("resource_uri")
        r_type = self.get_param("resource_type")
        if not r_uri or not r_type:
            return
        t = ModelService.get_model_type(r_type)
        resource = t.get(t.uri == r_uri)
        self.output["resource"] = resource
        

class Sink(Process):
    """
    Sink process.
    
    A sink process is used to recieve a resource. No action is done.
    """
    
    input_specs = {'resource' : (Resource, )}
    output_specs = {}
    config_specs = {}
    _is_plug = True
    
    async def task(self):
        pass

class FIFO2(Process):
    """
    FIFO2 process (with 2 input ports)

    The FIFO2 (First-In-First-Out) process sends to the output port the first resource received in an input port
    """

    input_specs = {'resource_1' : (Resource, None, ), 'resource_2' : (Resource, None, )}
    output_specs = {'resource' : (Resource, )}
    config_specs = {}
    _is_plug = True
    
    def check_before_task(self):
        res_1 = self.input['resource_1']
        res_2 = self.input['resource_2']
        is_ready = res_1 or res_2
        if not is_ready:
            return False

        return True

    async def task(self):
        resource = self.input["resource_1"]
        if resource:
            self.output["resource"] = resource
            return

        resource = self.input["resource_2"]
        if resource:
            self.output["resource"] = resource

class Switch2(Process):
    """
    Switch process (with 2 input ports)

    The Switch2 proccess sends to the output port the resource corresponding to the parameter `index`
    """

    input_specs = {'resource_1' : (Resource, None, ), 'resource_2' : (Resource, None, )}
    output_specs = {'resource' : (Resource, )}
    config_specs = {
        "index": {"type": int, "default": 1, "min": 1, "max": 2, "Description": "The index of the input resource to switch on. Defaults to 1."}
    }
    _is_plug = True
    
    async def task(self):
        index = self.get_param("index")
        resource = self.input[f"resource_{index}"]
        self.output["resource"] = resource

class Wait(Process):
    """
    Wait process

    This proccess waits during a given time before continuing.
    """

    input_specs = {'resource' : (Resource,)}
    output_specs = {'resource' : (Resource,)}
    config_specs = {
        "waiting_time": {"type": float, "default": 3, "min": 0, "Description": "The waiting time in seconds. Defaults to 3 second."}
    }
    _is_plug = True
    
    async def task(self):
        waiting_time = self.get_param("waiting_time")
        time.sleep(waiting_time)
        resource = self.input[f"resource"]
        self.output["resource"] = resource