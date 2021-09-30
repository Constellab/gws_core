# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...config.param_spec import BoolParam, StrParam
from ...task.task_decorator import task_decorator
from ..file.file import File
from ..file.file_uploader import (FileDumper, FileExporter, FileImporter,
                                  FileLoader)
from .json_dict import JSONDict

# ####################################################################
#
# Importer class
#
# ####################################################################


@task_decorator("JSONImporter")
class JSONImporter(FileImporter):
    input_specs = {'file': File}
    output_specs = {'data': JSONDict}
    config_specs = {
        'file_format': StrParam(default_value=".json", description="File format"),
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################


@task_decorator("JSONExporter")
class JSONExporter(FileExporter):
    input_specs = {'data': JSONDict}
    output_specs = {'file': File}
    config_specs = {
        'file_name': StrParam(default_value='file.json', description="Destination file name in the store"),
        'file_format': StrParam(default_value=".json", description="File format"),
        'prettify': BoolParam(default_value=False, description="True to indent and prettify the JSON file, False otherwise")
    }

# ####################################################################
#
# Loader class
#
# ####################################################################


@task_decorator("JSONLoader")
class JSONLoader(FileLoader):
    input_specs = {}
    output_specs = {'data': JSONDict}
    config_specs = {
        'file_path': StrParam(optional=True, description="Location of the file to import"),
        'file_format': StrParam(default_value=".json", description="File format")
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################


@task_decorator("JSONDumper")
class JSONDumper(FileDumper):
    input_specs = {'data': JSONDict}
    output_specs = {}
    config_specs = {
        'file_path': StrParam(optional=True, description="Destination of the exported file"),
        'file_format': StrParam(default_value=".csv", description="File format"),
        'prettify': BoolParam(default_value=False, description="True to indent and prettify the JSON file, False otherwise")
    }
