# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from gws.model import Resource

class JSONData(Resource):
    
    # -- A -- 

    # -- E --
    
    def _export(self, file_path: str, file_format:str = None):
        """ 
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """
        
        with open(file_path, "w") as f:
            json.dump(self.kv_data, f, indent=4)
            
    # -- G --
    
    def __getitem__(self, key):
        return self.kv_data[key]
    
    def get(self, key, default=None):
        return self.kv_data.get(key,default)
    
    # -- I --
    
    @classmethod
    def _import(cls, file_path: str, file_format:str = None) -> any:
        """ 
        Import a give from repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """
        
        with open(file_path, "r") as f:
            json_data = cls()
            json_data.kv_data = json.load(f)
        
        return json_data
    
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
    
    # -- K --
    
    @property
    def kv_data(self):
        if not 'kv_data' in self.data:
            self.data["kv_data"] = {}
            
        return self.data["kv_data"]
    
    @kv_data.setter
    def kv_data(self, kv_data: dict):
        self.data["kv_data"] = kv_data
    
    # -- S --
    
    # -- S --
    
    def _select(self, **params) -> 'Model':
        """ 
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """
        
        #@ToDo: ensure that this method is only called by an Selector
        
        pass
    
    def __setitem__(self, key, val):
        self.data[key] = val
