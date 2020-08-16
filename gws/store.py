# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import uuid
import shelve

class KVStore:
    """ 
    KVStore class representing a key-value object storage.

    This class allows serializing/deserializing huge objects on store.
    """

    _kv_data = None
    _path = None
    _file_name = 'data'

    # internal data for lazy storage
    __lazy_kv_data: dict = None

    # @todo
    # allow use of external object storage providers AWS S3, OVH cloud (OpenIO), MinIO, etc.
    _provider = None

    def __init__(self, path:str = None):
        self._path = path 
        self.__lazy_kv_data = {}
                
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
            raise Exception(f"The key must be a string. The actual value is {key}")

        if self.file_path is None:
            self.__lazy_kv_data[key] = value
        else:
            dir_path = os.path.dirname(self.file_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            self._kv_data = shelve.open(self.file_path)
            
            if bool(self.__lazy_kv_data):
                for k in self.__lazy_kv_data:
                    self._kv_data[k] = self.__lazy_kv_data[k]
                self.__lazy_kv_data = {}

            self._kv_data[key] = value

            self._kv_data.close()

    # -- C --

    def connect(self, path: str = None):
        """ 
        Connects the KVStore to a file

        :param path: The connection path
        :type path: str
        """
        if not isinstance(path, str) or path == "":
            raise Exception("The path must be a non-empty string.")

        self._path = path

        if bool(self.__lazy_kv_data):
            dir_path = os.path.dirname(self.file_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            self._kv_data = shelve.open(self.file_path)

            for k in self.__lazy_kv_data:
                self._kv_data[k] = self.__lazy_kv_data[k]
            self.__lazy_kv_data = {}

            self._kv_data.close()

        return True

    
    
    # -- F --

    @property
    def file_path(self) -> str:
        """ 
        PAth of the KVStore

        :return: The connection path
        :rtype: str
        """

        if self._path is None:
            return None
            
        return os.path.join(self._path, self._file_name)

    # -- G --

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise Exception(f"The key must be a string. The actual value is {key}")

        if self.file_path is None:
            return self.__lazy_kv_data.get(key, None)
        else:
            self._kv_data = shelve.open(self.file_path)
            val = self._kv_data.get(key, None)
            self._kv_data.close()
            return val

    # -- E --

    def is_connected(self):
        """ 
        Returns True if the KVStore is connected
        """
        return not (self.file_path is None)

    # -- P --

    def pop(self, key):
        if self.file_path is None:
            if key in self.__lazy_kv_data:
                val = self.__lazy_kv_data[key]
                del self.__lazy_kv_data[key]
        else:
            self._kv_data = shelve.open(self.file_path)
            if key in self._kv_data:
                val = self._kv_data[key]
                del self._kv_data[key]
            self._kv_data.close()
        
        return val
    
    # -- R --

    def remove(self, key):
        self.pop(key)
