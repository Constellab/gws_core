# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import json
import mimetypes
import os
import shutil
from pathlib import Path
from typing import List

from fastapi import UploadFile
from peewee import CharField

from gws.exception.bad_request_exception import BadRequestException

from .file_store import FileStore, LocalFileStore
from .process import Process
from .resource import Resource
from .resource_set import ResourceSet
from .settings import Settings
from .utils import generate_random_chars


class File(Resource):
    """
    File class
    """

    file_store_uri = CharField(null=True, index=True)
    path = CharField(null=True, index=True, unique=True)
    _mode = "t"
    _table_name = "gws_file"
    __DOWNLOAD_URL = "https://lab.{}/core-api/file/{}/{}/download"

    # -- D --

    def delete_instance(self, *args, **kwargs):
        with self._db_manager.db.atomic():
            status = super().delete_instance(*args, **kwargs)
            if status:
                shutil.rmtree(self.path)

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

    @property
    def file_store(self):
        if self.file_store_uri:
            fs = FileStore.get(FileStore.uri == self.file_store_uri).cast()
        else:
            try:
                fs = LocalFileStore.get_by_id(0)
            except:
                # create a default LocalFileStore
                fs = LocalFileStore()
                fs.save()
            self.file_store_uri = fs.uri
            self.save()

        return fs

    # -- I --

    def is_json(self):
        return self.extension in [".json"]

    def is_csv(self):
        return self.extension in [".csv", ".tsv"]

    def is_txt(self):
        return self.extension in [".txt"]

    def is_jpg(self):
        return self.extension in [".jpg", ".jpeg"]

    def is_png(self):
        return self.extension in [".png"]

    # -- M --

    @property
    def mime(self):
        ext = self.extension
        if ext:
            return mimetypes.types_map[self.extension]
        else:
            return None

    def move_to_store(self, fs: 'FileStore'):
        if not fs.contains(self):
            fs.add(self)

    def move_to_default_store(self):
        fs = LocalFileStore.get_default_instance()
        if not fs.contains(self):
            fs.add(self)

    # -- N --

    @property
    def name(self):
        return Path(self.path).name

    # -- O --

    def open(self, mode: str):
        """
        Open the file
        """

        if self.exists():
            return open(self.path, mode)
        else:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)
                if not os.path.exists(self.dir):
                    raise BadRequestException(
                        f"Cannot create directory {self.dir}")
            return open(self.path, mode="w+")

    # -- P --

    # -- R --

    def read(self):
        m = "r+"+self._mode
        with self.open(m) as fp:
            data = fp.read()
        return data

    def readline(self):
        m = "r+"+self._mode
        with self.open(m) as fp:
            data = fp.readline()
        return data

    def readlines(self, n=-1):
        m = "r+"+self._mode
        with self.open(m) as fp:
            data = fp.readlines(n)
        return data

    # -- T --

    def to_json(self, stringify: bool = False, prettify: bool = False, shallow: bool = True, **kwargs):
        _json = super().to_json(**kwargs)
        settings = Settings.retrieve()
        host = settings.data.get("host", "0.0.0.0")
        vhost = settings.data.get("virtual_host", host)
        _json["url"] = File.__DOWNLOAD_URL.format(vhost, self.type, self.uri)

        if not shallow:
            if self.is_json():
                _json["data"]["content"] = json.loads(self.read())
            else:
                _json["data"]["content"] = self.read()
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- W --

    def write(self, data: str, discard=False):
        """
        Write in the file
        """
        m = "a+"+self._mode
        with self.open(m) as fp:
            fp.write(data)

    # -- S --

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


class FileUploader(Process):
    input_specs = {}
    output_specs = {'result': (FileSet, File,)}
    config_specs = {
        'file_store_uri': {"type": str, "default": None, 'description': "URI of the file_store where the file must be downloaded"},
    }
    _files: list = None

    def __init__(self, *args, files: List[UploadFile] = [], **kwargs):
        super().__init__(self, *args, **kwargs)

        if not isinstance(files, list):
            raise BadRequestException(
                "A list of file-like objects is expected")

        self._files = files

    async def task(self):

        fs_uri = self.get_param("file_store_uri")
        if fs_uri:
            try:
                fs = FileStore.get(FileStore.uri == fs_uri).cast()
            except:
                raise BadRequestException(
                    f"No FileStore object found with uri '{file_store_uri}'")
        else:
            fs = LocalFileStore.get_default_instance()

        if len(self._files) == 1:
            file = self._files[0]
            f = fs.add(file.file, dest_file_name=file.filename)
            result = f
        else:
            result = FileSet()
            #t = self.out_port("file_set").get_default_resource_type()
            #file_set = t()
            for file in self._files:
                f = fs.add(file.file, dest_file_name=file.filename)
                result.add(f)

        self.output["result"] = result

    @staticmethod
    def uniquify(file_name: str):
        p = Path(file_name)
        file_name = p.stem + "_" + generate_random_chars() + p.suffix
        return file_name

# ####################################################################
#
# Importer class
#
# ####################################################################


class FileImporter(Process):
    input_specs = {'file': File}
    output_specs = {"data": Resource}
    config_specs = {
        'file_format': {"type": str, "default": None, 'description': "File format"},
        'output_type': {"type": str, "default": "", 'description': "The output file type. If defined, it is used to automatically format data output"},
    }

    async def task(self):
        file = self.input["file"]

        model_t = None
        if self.param_exists("output_type"):
            out_t = self.get_param("output_type")
            if out_t:
                from .service import ModelService
                model_t = ModelService.get_model_type(out_t)

        if not model_t:
            model_t = self.out_port("data").get_default_resource_type()

        params = copy.deepcopy(self.config.params)
        resource = model_t._import(file.path, **params)
        self.output["data"] = resource


# ####################################################################
#
# Exporter class
#
# ####################################################################

class FileExporter(Process):
    """
    File exporter. The file is writen in a file store
    """

    input_specs = {"data": Resource}
    output_specs = {'file': File}
    config_specs = {
        'file_name': {"type": str, "default": 'file', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
        'file_store_uri': {"type": str, "default": None, 'description': "URI of the file_store where the file must be exported"},
    }

    async def task(self):
        fs_uri = self.get_param("file_store_uri")
        if fs_uri:
            try:
                fs = FileStore.get(FileStore.uri == fs_uri).cast()
            except:
                raise BadRequestException(
                    f"No FileStore object found with uri '{file_store_uri}'")
        else:
            fs = LocalFileStore.get_default_instance()

        filename = self.get_param("file_name")
        t = self.out_port("file").get_default_resource_type()
        file = fs.create_file(name=filename, file_type=t)

        if not os.path.exists(file.dir):
            os.makedirs(file.dir)

        if "file_name" in self.config.params:
            params = copy.deepcopy(self.config.params)
            del params["file_name"]
        else:
            params = self.config.params

        resource = self.input["data"]
        resource._export(file.path, **params)
        self.output["file"] = file

# ####################################################################
#
# Loader class
#
# ####################################################################


class FileLoader(Process):
    input_specs = {}
    output_specs = {"data": Resource}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
        'output_type': {"type": str, "default": "", 'description': "The output file type. If defined, it is used to automatically format data output"},
    }

    async def task(self):
        file_path = self.get_param("file_path")

        model_t = None
        if self.param_exists("output_type"):
            out_t = self.get_param("output_type")
            if out_t:
                from .service import ModelService
                model_t = ModelService.get_model_type(out_t)

        if not model_t:
            model_t = self.out_port("data").get_default_resource_type()

        if "file_path" in self.config.params:
            params = copy.deepcopy(self.config.params)
            del params["file_path"]
        else:
            params = self.config.params

        resource = model_t._import(file_path, **params)
        self.output["data"] = resource

# ####################################################################
#
# Dumper class
#
# ####################################################################


class FileDumper(Process):
    """
    Generic data exporter
    """

    input_specs = {"data": Resource}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": None, 'description': "File format"},
    }

    async def task(self):
        file_path = self.get_param("file_path")
        resource = self.input["data"]

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
