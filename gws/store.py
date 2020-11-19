# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import uuid
import shelve
from gws.logger import Logger

class KVStore:
    """ 
    KVStore class representing a key-value object storage.
    This class allows serializing/deserializing huge objects on store.
    """

    _kv_data = None
    _path = None
    _file_name = 'data'

    # @todo
    # allow use of external object storage providers AWS S3, OVH cloud (OpenIO), MinIO, etc.
    _provider = None

    def __init__(self, path:str = None):
        self._path = path 
                
    # -- A --

    def __setitem__(self, key, value):
        """ 
        Adds a new object value to the KVStore

        :param key: The key of the object
        :type ket: str
        :param value: The value of the object
        :type value: any
        """
        if not isinstance(key, str):
            Logger.error(Exception(f"The key must be a string. The actual value is {key}"))

        dir_path = os.path.dirname(self.file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        self._kv_data = shelve.open(self.file_path)
        self._kv_data[key] = value
        self._kv_data.close()

    # -- S --
    
    # -- F --

    @property
    def file_path(self) -> str:
        """ 
        Path of the KVStore

        :return: The connection path
        :rtype: str
        """

        if self._path is None:
            return None
            
        return os.path.join(self._path, self._file_name)

    # -- G --

    def __getitem__(self, key):
        if not isinstance(key, str):
            Logger.error(Exception(f"The key must be a string. The actual value is {key}"))

        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data.get(key, None)
        self._kv_data.close()
        return val

    # -- E --

    # -- P --

    def pop(self, key):

        self._kv_data = shelve.open(self.file_path)
        if key in self._kv_data:
            val = self._kv_data[key]
            del self._kv_data[key]

        self._kv_data.close()
        return val
    
    # -- R --

    def remove(self, key):
        self.pop(key)
