# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import io
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
from gws.store import FileStore
from gws.utils import slugify, generate_random_chars

class File(Resource):
    path = CharField(null=False, index=True)
    _file_store: FileStore = FileStore()
    _table_name = "gws_file"
    
    def move(self, dest_path: str):
        self._file_store.move(self.path, dest_path)
        self.path = dest_path
        self.save()
    
    def exists():
        return self._file_store.exists(dest_path)

class FileSet(ResourceSet):
    _resource_types = (File, )
    

class Uploader(Process):
    input_specs = {}
    output_specs = {'file_set' : FileSet}
    config_specs = {}
    _files: list = None
    
    def __init__(self, *args, files: List[UploadFile] = [], **kwargs):
        super().__init__(self, *args, **kwargs)
        
        if not isinstance(files, list):
            Logger.error(Exception("Uploader", "__init__", "A list of file-like objects is expected"))
        
        self._files = files
        
    def task(self):
        file_set = FileSet()
        for file in self._files:
            fs = FileStore()
            file_name = self.uniquify(file.filename)
            file_path = fs.push(file.file, dest_file_name=file_name, slot="uploads")
            f = File(path=file_path)
            f.save()
            file_set[file_name] = f
        
        self.output["file_set"] = file_set
    
    @staticmethod
    def uniquify(file_name:str):
        p = Path(file_name) 
        file_name = p.stem + "_" + generate_random_chars() + p.suffix
        return file_name
                
class Importer(Process):
    input_specs = {'file' : File}
    output_specs = {'resource' : Resource}
    config_specs = {
        'source_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
        'resource_type': {"type": str, "default": None, 'description': "Expected resource type"},
    }
    
    def task(self):
        t_str = self.get_param("resource_type")
        model_t = Controller.get_model_type(t_str)
        if model_t:
            try:
                resource = model_t._import(source_path)
            except Exception as err:
                Logger.error(Exception("Importer", "task", f"Could not import the resource. Error: {err}"))


class Exporter(Process):
    input_specs = {'resource' : Resource}
    output_specs = {}
    config_specs = {
        'destination_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
        'resource_type': {"type": str, "default": None, 'description': "Expected resource type"},
    }
    
    def task(self):
        resource = self.input['resource']
        try:
            resource._export(destination_path, output_type=resource_type)
        except Exception as err:
            Logger.error(Exception("Exporter", "task", f"Could not export the resource. Error: {err}"))