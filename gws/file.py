# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import copy
import pathlib
import json
import tempfile

from typing import List
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from peewee import  Field, IntegerField, FloatField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField, IPField, TextField, BlobField

from gws.settings import Settings
from gws.model import Config, Process, Resource, ResourceSet
from gws.controller import Controller
from gws.store import FileStore, LocalFileStore
from gws.utils import slugify, generate_random_chars
from gws.logger import Error

class File(Resource):
    file_store_uri = CharField(null=True, index=True)
    path = CharField(null=True, index=True, unique=True)
    #file_store = LocalFileStore()
    
    _fp = None
    _mode = "a+t"
    _table_name = "gws_file"
    
    # -- A --
    
    def as_json(self, stringify: bool=False, prettify: bool=False, read_content: bool=False, **kwargs):
        _json = super().as_json(**kwargs)
        if read_content:
            if self.is_json():
                _json["data"]["content"] = json.loads(self.read())
            #elif self.is_csv():
            #    df = pandas.read_table(
            #        self.path, 
            #        sep = kwargs.get("delimiter", "\t"),
            #        header = kwargs.get("header ", 0),
            #        index_col = kwargs.get("index_col ", None),
            #    )
            #    _json["data"]["content"] = json.loads(self.read())
            else:
                _json["data"]["content"] = self.read()
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
    # -- C --
    
    def clear(self):
        """ 
        Clear file content 
        """
        
        if self._fp:
            self.close()
            
        open(self.path, 'w').close()
    
    def close(self):
        """ 
        Close the file 
        """
  
        if self._fp:
            self._fp.close()
            self._fp = None
    
    # -- D --
    
    def delete_instance(self, *args, **kwargs):
        self.file_store.remove(self)            
        return super().delete_instance(*args, **kwargs)
    
    @property
    def dir(self):
        return Path(self.path).parent
    
    # -- E --
    
    @property
    def extension(self):
        return Path(self.path).suffix
    
    def exists(self):
        return os.path.exists(self.path)
    
    # -- F --
    
    def file_store(self):
        if self.file_store_uri:
            fs = FileStore.get( FileStore.uri==self.file_store_uri ).cast()
        else:
            try:
                fs = LocalFileStore.get_by_id(0)
            except:
                #create a default LocalFileStore
                fs = LocalFileStore()
                fs.save()
                
            self.file_store_uri = fs.uri
            self.save()
            
        return fs
        
    # -- I --
    
    def is_json( self ):
        return self.extension in [".json"]
    
    def is_csv( self ):
        return self.extension in [".csv", ".tsv"]
    
    def is_txt( self ):
        return self.extension in [".txt"]
    
    def is_jpg( self ):
        return self.extension in [".jpg", ".jpeg"]
    
    def is_png( self ):
        return self.extension in [".png"]
        
    # -- M --
    
    def move_to_store(self, fs: 'FileStore'):
        if not fs.contains(self):
            fs.add(self)
        
    # -- N --
    
    @property
    def name(self):
        return Path(self.path).name
    
    # -- O --
    
    def open(self, mode: str=None):
        """ 
        Open the file 
        
        """
 
        if not mode:
            mode = self._mode
        
        fs = self.file_store
        self._fp = fs.open(self)
        return self._fp
    
    # -- P --
    
    
    
    # -- R --
    
    def reopen(self, mode: str=None):
        self.close()
        return self.open(mode)
        
    def read(self):
        if not self._fp:
            self.open()  
        
        self._fp.seek(0)
        return self._fp.read()
    
    def readline(self):
        if not self._fp:
            self.open()  
            
        return self._fp.readline()
    
    def readlines(self, n=-1):
        if not self._fp:
            self.open()  
            
        return self._fp.readlines(n)
    
    # -- W --
    
    def write(self, data: str = None):
        """ 
        Write in the file 
        """
        
        if not self._fp:
            self.open()   
            
        self._fp.write(data)
    
    # -- S --
    
    
# ####################################################################
#
# TextFile class
#
# ####################################################################

class TextFile(File):
    pass

# ####################################################################
#
# BinaryFile class
#
# ####################################################################

class BinaryFile(File):
    _mode = "a+b"
    
# ####################################################################
#
# FileSet class
#
# ####################################################################

class FileSet(ResourceSet):
    _resource_types = (File, )
    
# ####################################################################
#
# Uploader class
#
# ####################################################################

class Uploader(Process):
    input_specs = {}
    output_specs = {'file_set' : FileSet}
    config_specs = {
        'file_store_uri': {"type": str, "default": None, 'description': "URI of the file_store where the file must be downloaded"},
    }
    _files: list = None
    
    def __init__(self, *args, files: List[UploadFile] = [], **kwargs):
        super().__init__(self, *args, **kwargs)
        
        if not isinstance(files, list):
            raise Error("Uploader", "__init__", "A list of file-like objects is expected")
        
        self._files = files
        
    async def task(self):
        
        fs_uri = self.get_param("file_store_uri")
        if fs_uri:
            try:
                fs = FileStore.get(FileStore.uri == fs_uri).cast()
            except:
                raise Error("Uploader", "task", f"No FileStore object found with uri '{file_store_uri}'")
        else:
            try:
                fs = LocalFileStore.get_by_id(0)
            except:
                fs = LocalFileStore()
                fs.save()
            
            
        t = self.out_port("file_set").get_default_resource_type()
        file_set = t()
        for file in self._files:
            f = fs.add(file.file, dest_file_name=file.filename)
            file_set.add(f)

        self.output["file_set"] = file_set
    
    @staticmethod
    def uniquify(file_name:str):
        p = Path(file_name) 
        file_name = p.stem + "_" + generate_random_chars() + p.suffix
        return file_name

# ####################################################################
#
# Importer class
#
# ####################################################################

class Importer(Process):
    input_specs = {'file' : File}
    output_specs = {'resource' : Resource}
    config_specs = {
        'file_format': {"type": str, "default": None, 'description': "File format"},
    }
    
    async def task(self):
        file = self.input["file"]
        model_t = self.out_port("resource").get_default_resource_type()
        params = copy.deepcopy(self.config.params)
        resource = model_t._import(file.path, **params)
        self.output["resource"] = resource
        
        
# ####################################################################
#
# Exporter class
#
# ####################################################################

class Exporter(Process):
    """
    File exporter. The file is writen in the file store
    """

    input_specs = {'resource' : Resource}
    output_specs = {'file' : File}
    config_specs = {
        'file_name': {"type": str, "default": 'file', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
    }
    
    async def task(self):
        filename = self.get_param("file_name")
        t = self.out_port("file").get_default_resource_type()
        file = t.file_store.create_file(name=filename)
        
        if not os.path.exists(file.dir):
            os.makedirs(file.dir)

        if "file_name" in self.config.params:
            params = copy.deepcopy(self.config.params)
            del params["file_name"]
        else:
            params = self.config.params

        resource = self.input['resource']
        resource._export(file.path, **params)
        self.output["file"] = file

# ####################################################################
#
# Loader class
#
# ####################################################################

class Loader(Process):
    input_specs = {}
    output_specs = {'resource' : Resource}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
    }
    
    async def task(self):
        file_path = self.get_param("file_path")
        model_t = self.out_port('resource').get_default_resource_type()
        
        if "file_path" in self.config.params:
            params = copy.deepcopy(self.config.params)
            del params["file_path"]
        else:
            params = self.config.params

        resource = model_t._import(file_path, **params)
        self.output["resource"] = resource

# ####################################################################
#
# Dumper class
#
# ####################################################################

class Dumper(Process):
    """
    Generic data exporter
    """
    
    input_specs = {'resource' : Resource}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
    }
    
    async def task(self):
        file_path = self.get_param("file_path")
        resource = self.input['resource']
        
        p = Path(file_path)
        parent_dir = p.parent
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        if "file_path" in self.config.params:
            params = copy.deepcopy(self.config.params)
            del params["file_path"]
        else:
            params = self.config.params

        resource._export(file_path, **params)  