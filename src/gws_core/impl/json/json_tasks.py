# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...config.param_spec import BoolParam, StrParam
from ...task.exporter import TaskExporter, exporter_decorator
from ...task.importer import TaskImporter, importer_decorator
from ...task.task_decorator import task_decorator
from ..file.file_uploader import FileDumper, FileLoader
from .json_dict import JSONDict

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="JSONImporter", resource_type=JSONDict)
class JSONImporter(TaskImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("FileExporter", resource_type=JSONDict)
class JSONExporter(TaskExporter):
    pass

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
        'file_path': StrParam(optional=True, short_description="Location of the file to import"),
        'file_format': StrParam(default_value=".json", short_description="File format")
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
        'file_path': StrParam(optional=True, short_description="Destination of the exported file"),
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'prettify': BoolParam(default_value=False, short_description="True to indent and prettify the JSON file, False otherwise")
    }
