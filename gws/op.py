# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.model import Resource, ResourceSet

class Selector(Resource):
    input_specs = {'resource' : Resource}
    output_specs = {'resource' : Resource}
    config_specs = {}
        
    def task(self):
        model_t = self.in_port('resource').get_default_resource_type()
    
        try:
            resource = model_t._extract(**self.config.params)
            self.output["resource"] = resource

        except Exception as err:
            raise Error("Extractor", "task", f"Could not extract the resource. Error: {err}")


class Joiner(Resource):
    input_specs = {'resource' : ResourceSet}
    output_specs = {'resource' : Resource}
    config_specs = {}
        
    def task(self):
        model_t = self.in_port('resource').get_default_resource_type()
    
        try:
            resource = model_t._extract(**self.config.params)
            self.output["resource"] = resource

        except Exception as err:
            raise Error("Extractor", "task", f"Could not extract the resource. Error: {err}")


    