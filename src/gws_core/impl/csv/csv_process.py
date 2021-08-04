
from ..file.file import File
from ..file.file_uploader import (FileDumper, FileExporter, FileImporter,
                                  FileLoader)
from .csv_resource import CSVTable

# ####################################################################
#
# Importer class
#
# ####################################################################


class CSVImporter(FileImporter):
    input_specs = {'file': File}
    output_specs = {'data': CSVTable}
    config_specs = {
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": '\t', "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": 'int', "default": None, "description": "Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"},
        'index': {"type": 'int', "default": None, "description": "Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################


class CSVExporter(FileExporter):
    input_specs = {'data': CSVTable}
    output_specs = {'file': File}
    config_specs = {
        'file_name': {"type": str, "default": 'file.csv', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": "\t", "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": bool, "default": True, "description":  "Write column names (header)"},
        'index': {"type": bool, "default": True, 'description': "Write row names (index)"},
        'file_store_uri': {"type": str, "default": None, 'description': "URI of the file_store where the file must be exported"},
    }

# ####################################################################
#
# Loader class
#
# ####################################################################


class CSVLoader(FileLoader):
    input_specs = {}
    output_specs = {'data': CSVTable}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": '\t', "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": 'int', "default": None, "description": "Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"},
        'index': {"type": 'int', "default": None, "description": "Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################


class CSVDumper(FileDumper):
    input_specs = {'data': CSVTable}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'delimiter': {"type": 'str', "default": "\t", "description": "Delimiter character. Only for parsing CSV files"},
        'header': {"type": bool, "default": True, "description":  "Write column names (header)"},
        'index': {"type": bool, "default": True, 'description': "Write row names (index)"},
    }
