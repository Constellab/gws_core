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

class KVStore:
    """ 
    KVStore class representing a key-value object storage.
    This class allows serializing/deserializing huge objects on store.
    """

    _kv_data = None
    _base_dir = None
    _folder_path = None
    _file_name = 'data'

    # @todo
    # allow use of external object storage providers AWS S3, OVHcloud (OpenIO), MinIO, etc.
    _provider = None

    def __init__(self, folder_path:str):
        db_dir = Controller.get_settings().get_data("db_dir")
        self._base_dir = os.path.join(db_dir, 'kv_store')
        
        while folder_path.startswith(".") or folder_path.startswith("/"):
            folder_path = folder_path.strip(".").strip("/")
            
        self._folder_path = folder_path
                
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
            raise Error(f"The key must be a string. The actual value is {key}")

        dir_path = os.path.dirname(self.file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        self._kv_data = shelve.open(self.file_path)
        self._kv_data[key] = value
        self._kv_data.close()

    # -- F --

    @property
    def file_path(self) -> str:
        """ 
        Path of the KVStore

        :return: The connection path
        :rtype: str
        """

        return os.path.join(self._base_dir, self._folder_path, self._file_name)

    # -- G --

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise Error(f"The key must be a string. The actual value is {key}")

        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data.get(key, None)
        self._kv_data.close()
        return val

    # -- E --

    # -- R --

    def delete(self, key):
        self._kv_data = shelve.open(self.file_path)
        if key in self._kv_data:
            val = self._kv_data[key]
            del self._kv_data[key]

        self._kv_data.close()
        return val
    
    def remove(self):        
        try:
            shutil.rmtree(self.file_path)
        except Exception as err:
            if not ignore_errors:
                raise Error("KVStore", "remove", f"Cannot remove the kv_store {self.file_path}")

class FileStore:
    _base_dir = None
    _auto_slot = False
    
    def __init__(self, base_dir: str = None):
        if not base_dir:
            db_dir = Controller.get_settings().get_data("db_dir")
            self._base_dir = os.path.join(db_dir, 'file_store') 
        else:
            self._base_dir = base_dir

    # -- A --
    
    # -- B --
 
    def __build_abs_file_path(self, file_path: str):
        file_path = self.__clean_file_path(file_path)
        return os.path.join(self._base_dir, file_path)
    
    # -- C --
    
    def __clean_file_path(self, file_path: str):
        while file_path.startswith(".") or file_path.startswith("/"):
            file_path = file_path.strip(".").strip("/")
        
        return file_path
    
    # -- E --
    
    def exists(self, file_path: str):
        file_path = self.__build_abs_file_path(file_path)       
        return os.path.exists(file_path)
    
    # -- M --
    
    def move(self, source_file_path: str, dest_file_path: str, force: bool=False):
        source_file_path = self.__build_abs_file_path(source_file_path) 
        dest_file_path = self.__build_abs_file_path(dest_file_path) 
        
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

    def push(self, source_file: (str, io.IOBase, ), dest_file_name="", slot: str="", force: bool=False):
        slot = self.__clean_file_path(slot)
        
        if isinstance(source_file, str):
            if not dest_file_name:
                dest_file_name = Path(source_file).name
                
        dest_dir = os.path.join(self._base_dir, slot)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            if not os.path.exists(dest_dir):
                raise Error("FileStore", "add", f"Cannot create directory {dest_dir}")

        dest_file_path = os.path.join(dest_dir, dest_file_name)
        if os.path.exists(dest_file_path) and not force:
            raise Error("FileStore", "add", f"The file already exists")
        
        if isinstance(source_file, str):
            shutil.copy2(source_file, dest_file_path)
        else:
            with open(dest_file_path, "wb") as buffer:
                shutil.copyfileobj(source_file, buffer)
        
        return os.path.join(slot,dest_file_name)

    
    # -- R --
    
    def remove(file_path: str, ignore_errors:bool = False):
        dest_file_path = self.__build_abs_file_path(dest_file_path) 
        
        try:
            shutil.rmtree(dest_file_path)
        except Exception as err:
            if not ignore_errors:
                raise Error("FileStore", "remove", f"Cannot remove file {file_path}. Error: {err}")
        
    def _remove_all_files(self, ignore_errors:bool = False):
        try:
            shutil.rmtree(self._base_dir)
        except Exception as err:
            if not ignore_errors:
                raise Error("FileStore", "remove_all_files", f"Cannot remove the store")
    