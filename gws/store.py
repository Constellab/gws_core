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
import tempfile

from gws.base import DbManager
from gws.model import Model
from gws.controller import Controller
from gws.logger import Error
from gws.settings import Settings

settings = Settings.retrieve()

# ####################################################################
#
# KVStore class
#
# ####################################################################

class KVStore:
    """ 
    KVStore class representing a key-value object storage engine.
    This class allows serializing/deserializing huge objects on store.
    """
    
    _kv_data = None
    _base_dir = settings.get_kv_store_dir()
    _slot_path = None    
    _file_name = 'data'

    def __init__(self, slot_path:str):
        super().__init__()
        
        while slot_path.startswith(".") or slot_path.startswith("/"):
            slot_path = slot_path.strip(".").strip("/")
            
        self._slot_path = slot_path
 
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
        Path of directory the KVStore object

        :return: The connection path
        :rtype: str
        """

        return os.path.join(self._base_dir, self._slot_path)
    
    # -- F --

    @property
    def file_path(self) -> str:
        """ 
        Path of DB file the KVStore object

        :return: The connection path
        :rtype: str
        :rtype: str
        """

        return os.path.join(self.dir_path, self._file_name)
    
  
    # -- G --
    
    def get(self, key, default=None):
        if not isinstance(key, str):
            raise Error(f"The key must be a string. The actual value is {key}")
        
        if not os.path.exists(self.dir_path):
            return default
        
        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data.get(key)
        self._kv_data.close()
        return val
    
    def __getitem__(self, key):
        if not isinstance(key, str):
            raise Error(f"The key must be a string. The actual value is {key}")
        
        if not os.path.exists(self.dir_path):
            raise Error("KVStore", "__getitem__", f"Key '{key}' does not exist")
        
        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data[key]
        self._kv_data.close()
        return val

    # -- R --

    def remove(self, ignore_errors=False):
        """ 
        Remove the store 
        """
        
        if not os.path.exists(self.dir_path):
            return
        
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

# ####################################################################
#
# FileStore class
#
# ####################################################################

class FileStore(Model):
    _table_name = "gws_file_store"
    
    # -- A --
    
    def add(self, source_file: (str, io.IOBase, tempfile.SpooledTemporaryFile, 'File', )):
        """ 
        Add a file from an external repository to a local store. Must be implemented by the child class.
        
        :param source_file: The source file
        :type source_file: `str` (file path), `gws.file.File`, `io.IOBase` or `tempfile.SpooledTemporaryFile`
        :param dest_file_name: The destination file name
        :type dest_file_name: `str`
        :return: The file object 
        :rtype: gws.file.File.
        """
        
        raise Error('FileStore','add', 'Not implemented')

    # -- O --
    
    @classmethod
    def open(cls, file, mode):
        """
        Open a file. Must be implemented by the child class.
        
        :param file: The file to open
        :type file: `gws.file.File`
        :param mode: Mode (see native Python `open` function)
        :type mode: `str`
        :return: The file object 
        :rtype: Python `file-like-object` or `stream`.
        """
        
        raise Error('FileStore','add', 'Not implemented')
    
    # -- P --
    
    @property
    def path(self) -> str:
        """ 
        Get path (or url) of the store
        """

        return self.data.get("path","")
    
    # -- F --

    @path.setter
    def path(self, path: str) -> str:
        """ 
        Set the path (or url) of the store
        """

        self.data["path"] = path
        
# ####################################################################
#
# RemoteFileStore class
#
# ####################################################################

class RemoteFileStore(FileStore):
    
    _default_container_url = ""
    
    def __init__(self, path=""):
        super().__init__(path=path)
            
    def add(self, source_file: (str, io.IOBase, tempfile.SpooledTemporaryFile, 'File', )):
        import requests
        from gws.file import File
        f = File()
        f.path = ""
        f.save()
        
        if isinstance(source_file, str):
            source_file = open(source_file ,'rb')
                
        files = {'file': source_file}
        response = requests.post(self.path, files = files)

        return f
    
    
# ####################################################################
#
# LocalFileStore class
#
# ####################################################################

class LocalFileStore(FileStore):
    
    _base_dir = settings.get_file_store_dir()
    
    def __init__(self):
        super().__init__()
 
        if not self.is_saved():
            self.save()
            if self.id == 1:
                self.data["title"] = "Default store"
                self.save()
        
        if not self.path:
            path =  os.path.join(self._base_dir, self.uri)
            self.data["path"] = path
            self.save()
      
    # -- A --

    def add(self, source_file: (str, io.IOBase, tempfile.SpooledTemporaryFile, 'File', ), \
                   dest_file_name: str=""):
        """ 
        Add a file from an external repository to a local store 
        
        :param source_file: The source file
        :type source_file: `str` (file path), `gws.file.File`, `io.IOBase` or `tempfile.SpooledTemporaryFile`
        :param dest_file_name: The destination file name
        :type dest_file_name: `str`
        :return: The file object 
        :rtype: gws.file.File.
        """
        
        if not self.is_saved():
            self.save()
            
        from gws.file import File     
        with DbManager.db.atomic() as transaction:
            
            try:
                # create DB file object
                if isinstance(source_file, File):
                    if self.contains(source_file):
                        return source_file
                
                    f = source_file
                    source_file_path = f.path

                    if not dest_file_name:
                        dest_file_name = Path(source_file_path).name

                    f.path = self.__create_valid_file_path(f, name=dest_file_name)
                else:
                    if not dest_file_name:
                        if isinstance(source_file, str):
                            dest_file_name = Path(source_file).name
                        else:
                            dest_file_name = "file"

                    f = self.create_file( name=dest_file_name )
                    source_file_path = source_file

                
                # copy disk file
                if not os.path.exists(f.dir):
                    os.makedirs(f.dir)
                    if not os.path.exists(f.dir):
                        raise Exception("FileStore", "add", f"Cannot create directory '{f.dir}'")

                if isinstance(source_file, (io.IOBase, tempfile.SpooledTemporaryFile, )):
                    with open(f.path, "wb") as buffer:
                        shutil.copyfileobj(source_file, buffer)
                else:
                    shutil.copy2(source_file_path, f.path)
                
                # save DB file object
                f.file_store_uri = self.uri
                f.save()
                return f

            except Exception as err:
                transaction.rollback()
                raise Error("FileStore", "add", f"An error occured. Error: {err}")

    # -- B --
    
    # -- C --
    
    def __create_valid_file_path( self, file: 'File', name: str  = ""):
        if not file.uri:
            file.save()
        
        file.path = os.path.join(self.path, file.uri, name)
        file.save()
        
        return file.path

    def create_file( self, name: str, file_type: type = None ):
        from gws.file import File
        
        if isinstance(file_type, type):
            file = file_type()
        else:
            file = File()
            
        self.__create_valid_file_path(file, name) 
        file.save()
        return file
     
    def contains(self, file: 'File') -> bool:
        return self.path in file.path
    
    # -- E --
  
    # -- G --
    
    @classmethod
    def get_default_instance(cls):
        try:
            fs = cls.get_by_id(1)
        except:
            fs = cls()
            fs.save()
            
        return fs
                
    #def get_real_path(self, location: str):
    #    location = self.__clean_file_path(location)
    #    return os.path.join(self.path, location)
    
    # -- I --
  
    # -- M --     
    
    # -- P --
    
    @property
    def path(self) -> str:
        """ 
        Get path of the local file store
        """
        
        return super().path
    
    # -- F --

    @path.setter
    def path(self, path: str) -> str:
        """ 
        Locked method.
        The path of a LocalFileStore is automatically computed and cannot be manually altered.
        """

        raise Error("LocalFileStore", "path", "Cannot manually set LocalFileStore path")

    
    # -- R --
    
    def remove(self, file: 'File', ignore_errors:bool = False):
        with DbManager.db.atomic() as transaction:
            try:
                if self.contains(file):
                    file.remove()
                    shutil.rmtree(file.path)
                else:
                    raise Exception("FileStore", "remove", f"The file is not in the store")
            except Exception as err:
                transaction.rollback()
                if not ignore_errors:
                    raise Error("FileStore", "remove", f"Cannot remove file {file.path} in file store. Error: {err}")
    
    @classmethod
    def remove_all_files(cls, ignore_errors:bool = False):
        from gws.query import Paginator
        with DbManager.db.atomic() as transaction:
            try:
                page = 1
                paginator = Paginator( cls.select(), page=page, number_of_items_per_page=500 )
                while len(paginator.current_items()):
                    for fs in paginator.current_items():
                        Q2 = File.select().where( File.file_store_uri == fs.uri )
                        for f in Q2:
                            f.remove()

                        shutil.rmtree(fs.path)
                    
                    page = page + 1
                    paginator = Paginator( cls.select(), page=page, number_of_items_per_page=500 )
                    
            except Exception as err:
                transaction.rollback()
                if not ignore_errors:
                    raise Error("FileStore", "remove_all_files", f"Cannot remove the store")
