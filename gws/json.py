# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from gws.model import Resource

class JSONData(Resource):
    
    # -- E --
    
    def _export(self, dest_file: str, file_format:str = None):
        """ 
        Export to a give repository

        :param dest_file: The destination file
        :type dest_file: File
        """
        
        with open(dest_file, "w") as f:
            json.dump(self.kv_data, f, indent=4)
            
    # -- G --
    
    def __getitem__(self, key):
        return self.kv_data[key]
    
    def get(self, key, default=None):
        return self.kv_data.get(key,default)
    
    # -- I --
    
    def _import(self, source_file: str, file_format:str = None) -> any:
        """ 
        Import a give from repository

        :param source_file: The source file
        :type source_file: File
        :returns: the parsed data
        :rtype any
        """
        
        with open(source_file, "r") as f:
            self.data = {}
            self.kv_data = json.load(f)
    
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
    
    def __setitem__(self, key, val):
        self.data[key] = val