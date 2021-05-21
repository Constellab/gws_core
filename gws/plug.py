# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws.model import Process, Resource

class Source(Process):
    """
    Source class. 
    
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
        from gws.service import ModelService
        
        r_uri = self.get_param("resource_uri")
        r_type = self.get_param("resource_type")
        
        t = ModelService.get_model_type(r_type)
        resource = t.get(t.uri == r_uri)
        
        self.output["resource"] = resource
        

class Sink(Process):
    """
    Sink class. 
    
    A sink process is used to recieve a resource. No action is done.
    """
    
    input_specs = {'resource' : (Resource, )}
    output_specs = {}
    config_specs = {} 
    
    _is_plug = True
    
    async def task(self):
        pass