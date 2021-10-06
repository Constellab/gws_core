
from gws_core.config.param_spec import BoolParam, IntParam, StrParam

from ...task.task_decorator import task_decorator
from ..file.file import File
from ..file.file_uploader import (FileDumper, FileExporter, FileImporter,
                                  FileLoader)
from .text import Text

# ####################################################################
#
# Importer class
#
# ####################################################################


@task_decorator(unique_name="TextImporter")
class TextImporter(FileImporter):
    input_specs = {'file': File}
    output_specs = {'data': Text}
    config_specs = {
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding")
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################


@task_decorator(unique_name="TextExporter")
class TextExporter(FileExporter):
    input_specs = {'data': Text}
    output_specs = {'file': File}
    config_specs = {
        'file_name': StrParam(default_value='file.txt', short_description="Destination file name in the store"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding"),
        'file_store_uri': StrParam(optional=True, short_description="URI of the file_store where the file must be exported"),
    }

# ####################################################################
#
# Loader class
#
# ####################################################################


@task_decorator(unique_name="TextLoader")
class TextLoader(FileLoader):
    input_specs = {}
    output_specs = {'data': Text}
    config_specs = {
        'file_path': StrParam(optional=True, short_description="Location of the file to import"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding")
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################


@task_decorator(unique_name="TextDumper")
class TextDumper(FileDumper):
    input_specs = {'data': Text}
    output_specs = {}
    config_specs = {
        'file_path': StrParam(optional=True, short_description="Destination of the exported file"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding")
    }
