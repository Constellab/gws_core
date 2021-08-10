# ####################################################################
#
# Uploader class
#
# ####################################################################

import copy
import os
from pathlib import Path
from typing import List

from fastapi import UploadFile
from fastapi.datastructures import UploadFile

from ...core.exception.exceptions import BadRequestException
from ...core.model.model import Model
from ...core.utils.utils import Utils
from ...model.typing_manager import TypingManager
from ...process.process import Process
from ...process.process_decorator import ProcessDecorator
from ...resource.resource import Resource
from .file import File, FileSet
from .file_store import FileStore, LocalFileStore


@ProcessDecorator("FileUploader")
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
                resource: Resource = FileStore.get(FileStore.uri == fs_uri)
                fs = TypingManager.get_object_with_typing_name(
                    resource.typing_name, resource.id)
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
        file_name = p.stem + "_" + Utils.generate_random_chars() + p.suffix
        return file_name

# ####################################################################
#
# Importer class
#
# ####################################################################


@ProcessDecorator("FileImporter")
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
                model_t = Model.get_model_type(out_t)

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
@ProcessDecorator("FileExporter")
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
                resource: Resource = FileStore.get(FileStore.uri == fs_uri)
                fs = TypingManager.get_object_with_typing_name(
                    resource.typing_name, resource.id)
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


@ProcessDecorator("FileLoader")
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
                model_t = Model.get_model_type(out_t)

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


@ProcessDecorator("FileDumper")
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
