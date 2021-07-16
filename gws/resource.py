# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from peewee import  IntegerField, CharField
from .db.model import Model
from .process import Process
from .viewable import Viewable

class Resource(Viewable):
    """
    Resource class.
    
    :property process: The process that created he resource
    :type process: Process
    """
    
    _process = None
    _experiment = None
    _table_name = 'gws_resource'
    
    def __init__(self, *args, process: 'Process'=None, experiment: 'Experiment'=None, **kwargs):
        super().__init__(*args, **kwargs)
        if process:
            self.process = process
        if experiment:
            self.experiment = experiment
    
    # -- C --
    
    @classmethod
    def create_resource_type(cls):
        from .typing import ResourceType
        exist = ResourceType.select().where(ResourceType.model_type == cls.full_classname()).count()
        if not exist:
            rt = ResourceType(
                model_type = cls.full_classname(),
                root_model_type = "gws.model.Resource"  
            )
            rt.save()
            
    # -- D --

    @classmethod
    def drop_table(cls, *args, **kwargs):
        super().drop_table(*args, **kwargs)
        ProcessResource.drop_table()
        ExperimentResource.drop_table()
    
    # -- E --
    
    @property
    def experiment(self):
        if not self._experiment:        
            try:
                o = ExperimentResource.get( (ExperimentResource.resource_id == self.id) & (ExperimentResource.resource_type == self.type) )
                self._experiment = o.experiment
            except:
                return None
        
        return self._experiment
        
    @experiment.setter
    def experiment(self, experiment: 'Experiment'):
        if self.experiment:
            return
        
        if not self.id:
            self.save()
            
        o = ExperimentResource(
            experiment_id=experiment.id,
            resource_id=self.id,
            resource_type=self.type, 
        )
        o.save()
        self._experiment = experiment
        
    def _export(self, file_path: str, file_format:str = None):
        """ 
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """
        
        #@ToDo: ensure that this method is only called by an Exporter
        
        pass
    
    # -- G --

    # -- I --
    
    @classmethod
    def _import(cls, file_path: str, file_format:str = None) -> any:
        """ 
        Import a resource from a repository. Must be overloaded by the child class.

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype any
        """
        
        #@ToDo: ensure that this method is only called by an Importer 
        
        pass
    
    # -- J --
    
    @classmethod
    def _join(cls, *args, **params) -> 'Model':
        """ 
        Join several resources

        :param params: Joining parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Joiner
        
        pass
    
    # -- P --
    
    @property
    def process(self):
        if not self._process:
            try:
                o = ProcessResource.get( (ProcessResource.resource_id == self.id) & (ProcessResource.resource_type == self.type) )
                self._process = o.process
            except Exception as _:
                return None
        
        return self._process
    
    @process.setter
    def process(self, process: Process):
        if self.process:
            return
        
        if not self.id:
            self.save()
            
        o = ProcessResource(
            process_id=process.id, 
            resource_id=self.id,
            resource_type=self.type, 
        )
        o.save()
        self._process = process
    
    # -- R --
    
    # -- S --
       
    def _select(self, **params) -> 'Model':
        """ 
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Selector
        
        pass
    
    # -- T --
    
    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(shallow=shallow,**kwargs)
        if self.experiment:
            _json.update({
                "experiment": {"uri": self.experiment.uri},
                "process": {
                    "uri": self.process.uri,
                    "type": self.process.type,
                },
            })
        if shallow:
            del _json["data"]  
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
    
    # -- V --

class ExperimentResource(Model):
    experiment_id = IntegerField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_type = CharField(null=False, index=True)
    _table_name = "gws_experiment_resource"
    
    @property
    def resource(self):
        from .service.model_service import ModelService
        t = ModelService.get_model_type(self.resource_type)
        return t.get_by_id(self.resource_id)
    
    @property
    def experiment(self):
        from .experiment import Experiment
        return Experiment.get_by_id(self.experiment_id)
    
    class Meta:
        indexes = (
            (("experiment_id", "resource_id", "resource_type"), True),
        )

class ProcessResource(Model):
    process_id = IntegerField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_type = CharField(null=False, index=True)
    _table_name = "gws_process_resource"
  
    @property
    def resource(self):
        from .service.model_service import ModelService
        t = ModelService.get_model_type(self.resource_type)
        return t.get_by_id(self.resource_id)
    
    @property
    def process(self):
        from .process import Process
        return Process.get_by_id(self.process_id)

    class Meta:
        indexes = (
            (("process_id", "resource_id", "resource_type"), True),
        )