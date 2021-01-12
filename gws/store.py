# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import io
import os
from pathlib import Path
import uuid
import shelve
import shutil

from gws.controller import Controller
from gws.logger import Error
from gws.settings import Settings

settings = Settings.retrieve()

db_dir = Controller.get_settings().get_data("db_dir")
kv_store_path = 'test_kv_store' if settings.is_test else 'prod_kv_store'
file_store_path = 'test_file_store' if settings.is_test else 'prod_file_store'
    
class KVStore:
    """ 
    KVStore class representing a key-value object storage engine.
    This class allows serializing/deserializing huge objects on store.
    """

    _kv_data = None
    _base_dir = os.path.join(db_dir, kv_store_path)
    _folder_path = None    
    _file_name = 'data'

    # @todo
    # allow use of external object storage providers AWS S3, OVHcloud (OpenIO), MinIO, etc.
    _provider = None

    def __init__(self, folder_path:str):
        while folder_path.startswith(".") or folder_path.startswith("/"):
            folder_path = folder_path.strip(".").strip("/")
            
        self._folder_path = folder_path
 
    # -- A --
    
    # -- D --
    
    def delete(self, key):
        """ Delete a key """
        self._kv_data = shelve.open(self.file_path)
        if key in self._kv_data:
            val = self._kv_data[key]
            del self._kv_data[key]

        self._kv_data.close()
        return val
    
    @property
    def dir_path(self) -> str:
        """ 
        Path of director the KVStore object

        :return: The connection path
        :rtype: str
        """

        return os.path.join(self._base_dir, self._folder_path)
    
    # -- F --

    @property
    def file_path(self) -> str:
        """ 
        Path of DB file the KVStore object

        :return: The connection path
        :rtype: str
        """

        return os.path.join(self._base_dir, self._folder_path, self._file_name)
    
    

    
    # -- G --
    
    def get(self, key, default=None):
        if not isinstance(key, str):
            raise Error(f"The key must be a string. The actual value is {key}")
        
        if not os.path.exists(self.dir_path):
            return default
        
        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data.get(key, default)
        self._kv_data.close()
        return val

    
    def __getitem__(self, key):
        if not isinstance(key, str):
            raise Error(f"The key must be a string. The actual value is {key}")
        
        if not os.path.exists(self.dir_path):
            raise Error("KVStore", "__getitem__", f"Key {key} does not exist")
        
        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data[key]
        self._kv_data.close()
        return val

    # -- R --

    def remove(self):
        """ 
        Remove the store 
        """
        
        try:
            shutil.rmtree(self.dir_path)
        except Exception as err:
            if not ignore_errors:
                raise Error("KVStore", "remove", f"Cannot remove the kv_store {self.dir_path}")
    
    @classmethod
    def remove_all(cls, folder:str = "", ignore_errors=False):
        """ 
        Remove the all stores in the base_dir 
        """
        
        _path = os.path.join(cls._base_dir,folder)
        if not os.path.exists(_path):
            return
        
        try:
            shutil.rmtree(_path)
        except Exception as err:
            if not ignore_errors:
                raise Error("KVStore", "remove", f"Cannot remove the kv_store {_path}")
    
    
    # -- S --
    
    def __setitem__(self, key, value):
        """ 
        Adds a new object value to the KVStore

        :param key: The key of the object
        :type ket: str
        :param value: The value of the object
        :type value: any
        """
        if not isinstance(key, str):
            raise Error(f"The key must be a string. The actual value is {key}")

        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        self._kv_data = shelve.open(self.file_path)
        self._kv_data[key] = value
        self._kv_data.close()
        
class FileStore:
    _base_dir = os.path.join(db_dir, file_store_path)
    
    # -- A --
    
    # -- B --
    
    # -- C --
    
    @classmethod
    def create_file( cls, name: str ):
        from gws.file import File
        f = File()
        f.save()
        
        f.path = os.path.join(cls._base_dir, f._table_name, f.uri, name)
        f.save()
        
        return f
    
    def contains(self, file: 'File') -> bool:
        return self._base_dir in file.path
    
    # -- E --
    
    def exists(self, location: str):
        file_path = self.get_real_path(location)       
        return os.path.exists(file_path)
    
    # -- G --
    
    def get_real_path(self, location: str):
        location = self.__clean_file_path(location)
        return os.path.join(self._base_dir, location)
    
    # -- M --
    
    def move(self, source_location: str, dest_location: str, force: bool=False):
        """ Move a file in the store """
        
        source_file_path = self.get_real_path(source_location) 
        dest_file_path = self.get_real_path(dest_location) 
        
        if os.path.exists(dest_file_path) and not force:
            raise Error("FileStore", "move", f"The destination file already exists")
        
        dest_dir = Path(dest_file_path).parent
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            if not os.path.exists(dest_dir):
                raise Error("FileStore", "move", f"Cannot create directory {dest_dir}")

        shutil.move(source_file_path, dest_file_path)
        
        source_dir = Path(source_file_path).parent
        while True:
            if len(os.listdir(source_dir)) == 0:
                shutil.rmtree(source_dir)
                source_dir = Path(source_dir).parent
                if source_dir == self._base_dir:
                    break
            else:
                break
    
    # -- P --

    def push(self, source_file: (str, io.IOBase, ), dest_file_name: str="", force: bool=False):
        """ Push a file from an external repository to the store """
        
        if isinstance(source_file, str):
            if not dest_file_name:
                dest_file_name = Path(source_file).name
                    
        f = self.create_file( name=dest_file_name )

        try:
            if not os.path.exists(f.dir):
                os.makedirs(f.dir)
                if not os.path.exists(f.dir):
                    raise Exception("FileStore", "push", f"Cannot create directory {f.dir}")

            if isinstance(source_file, str):
                shutil.copy2(source_file, f.path)
            else:
                with open(f.path, "wb") as buffer:
                    shutil.copyfileobj(source_file, buffer)

            return f
        
        except Exception as err:
            f.delete_instance()
            raise Error("FileStore", "push", f"An error occured. Error: {err}")

    
    # -- R --
    
    @classmethod
    def remove(cls, file: 'File', ignore_errors:bool = False):
        try:
            if cls.contains(file):
                shutil.rmtree(file.path)
            else:
                raise Exception("FileStore", "remove", f"The file path is outside the store")
        except Exception as err:
            if not ignore_errors:
                raise Error("FileStore", "remove", f"Cannot remove file {file.path} in file store. Error: {err}")
    
    @classmethod
    def remove_all_files(self, ignore_errors:bool = False):
        
        if not os.path.exists(self._base_dir):
            return
        
        try:
            shutil.rmtree(self._base_dir)
        except Exception as err:
            if not ignore_errors:
                raise Error("FileStore", "remove_all_files", f"Cannot remove the store")
    