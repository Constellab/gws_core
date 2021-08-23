# ####################################################################
#
# Uploader class
#
# ####################################################################

import copy
import os
from pathlib import Path
from typing import Type

from ...config.config_params import ConfigParams
from ...core.utils.utils import Utils
from ...process.process import Process
from ...process.process_decorator import ProcessDecorator
from ...process.process_io import ProcessIO
from ...progress_bar.progress_bar import ProgressBar
from ...resource.resource import Resource
from .file import File
from .file_resource import FileResource
from .file_store import LocalFileStore

# ####################################################################
#
# Importer class
#
# ####################################################################


@ProcessDecorator("FileImporter")
class FileImporter(Process):
    input_specs = {'file': File}
    output_specs = {"data": Resource}
    config_specs = {'file_format': {"type": str, "default": None, 'description': "File format"}, 'output_type': {
        "type": str, "default": "", 'description': "The output file type. If defined, it is used to automatically format data output"}, }

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        inport_name = list(self.input.keys())[0]
        outport_name = list(self.output.keys())[0]
        file: File = inputs[inport_name]

        model_t: Type[Resource] = None
        if config.param_exists("output_type"):
            out_t = config.get_param("output_type")
            if out_t:
                model_t = Utils.get_model_type(out_t)

        if not model_t:
            model_t = self.get_default_output_spec_type(outport_name)

        params = copy.deepcopy(config)
        resource = model_t.import_resource(file.path, **params)
        return {outport_name: resource}


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

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:

        file_store: LocalFileStore
        if config.param_exists('file_store_uri'):
            file_store = LocalFileStore.get_by_uri_and_check(config.get('file_store_uri'))
        else:
            file_store = LocalFileStore.get_default_instance()

        inport_name = list(self.input.keys())[0]
        outport_name = list(self.output.keys())[0]
        filename = config.get_param("file_name")
        file_type: Type[File] = self.get_default_output_spec_type("file")
        file: File = file_store.create_file(name=filename, file_type=file_type)

        if not os.path.exists(file.dir):
            os.makedirs(file.dir)

        if "file_name" in config:
            params = copy.deepcopy(config)
            del params["file_name"]
        else:
            params = config

        resource: Resource = inputs[inport_name]
        resource.export(file.path, **params)
        return {outport_name: file}

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
        'output_type':
        {"type": str, "default": "",
         'description': "The output file type. If defined, it is used to automatically format data output"}, }

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        outport_name = list(self.output.keys())[0]
        file_path = config.get_param("file_path")

        model_t: Type[Resource] = None
        if config.param_exists("output_type"):
            out_t = config.get_param("output_type")
            if out_t:
                model_t = Utils.get_model_type(out_t)

        if not model_t:
            model_t = self.get_default_output_spec_type(outport_name)

        if "file_path" in config:
            params = copy.deepcopy(config)
            del params["file_path"]
        else:
            params = config

        resource = model_t.import_resource(file_path, **params)
        return {outport_name: resource}

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

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        file_path = config.get_param("file_path")
        inport_name = list(self.input.keys())[0]
        resource: Resource = inputs[inport_name]

        p = Path(file_path)
        parent_dir = p.parent
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        if "file_path" in config:
            params = copy.deepcopy(config)
            del params["file_path"]
        else:
            params = config

        resource.export(file_path, **params)
