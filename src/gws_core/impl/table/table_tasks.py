
from gws_core.config.param_spec import BoolParam, IntParam, StrParam

from ...task.task_decorator import task_decorator
from ..file.file import File
from ..file.file_uploader import (FileDumper, FileExporter, FileImporter,
                                  FileLoader)
from .table import Table

# ####################################################################
#
# Importer class
#
# ####################################################################


@task_decorator(unique_name="TableImporter")
class TableImporter(FileImporter):
    input_specs = {'file': File}
    output_specs = {'data': Table}
    config_specs = {
        'file_format': StrParam(default_value=".csv", description="File format"),
        'delimiter': StrParam(default_value='\t', description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, description="Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"),
        'index': IntParam(optional=True, description="Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"),
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################


@task_decorator(unique_name="TableExporter")
class TableExporter(FileExporter):
    input_specs = {'data': Table}
    output_specs = {'file': File}
    config_specs = {
        'file_name': StrParam(default_value='file.csv', description="Destination file name in the store"),
        'file_format': StrParam(default_value=".csv", description="File format"),
        'delimiter': StrParam(default_value="\t", description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, description="Write column names (header)"),
        'index': BoolParam(default_value=True, description="Write row names (index)"),
        'file_store_uri': StrParam(optional=True, description="URI of the file_store where the file must be exported"),
    }

# ####################################################################
#
# Loader class
#
# ####################################################################


@task_decorator(unique_name="TableLoader")
class TableLoader(FileLoader):
    input_specs = {}
    output_specs = {'data': Table}
    config_specs = {
        'file_path': StrParam(optional=True, description="Location of the file to import"),
        'file_format': StrParam(default_value=".csv", description="File format"),
        'delimiter': StrParam(default_value='\t', description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, description="Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"),
        'index': IntParam(optional=True, description="Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"),
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################


@task_decorator(unique_name="TableDumper")
class TableDumper(FileDumper):
    input_specs = {'data': Table}
    output_specs = {}
    config_specs = {
        'file_path': StrParam(optional=True, description="Destination of the exported file"),
        'file_format': StrParam(default_value=".csv", description="File format"),
        'delimiter': StrParam(default_value="\t", description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, description="Write column names (header)"),
        'index': BoolParam(default_value=True, description="Write row names (index)"),
    }
