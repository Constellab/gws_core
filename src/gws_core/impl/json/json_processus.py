from ...resource.file.file import File
from ...resource.file.file_uploader import (FileDumper, FileExporter,
                                            FileImporter, FileLoader)
from .json_resource import JSONDict

# ####################################################################
#
# Importer class
#
# ####################################################################


class JSONImporter(FileImporter):
    input_specs = {'file': File}
    output_specs = {'data': JSONDict}
    config_specs = {
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################


class JSONExporter(FileExporter):
    input_specs = {'data': JSONDict}
    output_specs = {'file': File}
    config_specs = {
        'file_name': {"type": str, "default": 'file.json', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
        'prettify': {"type": bool, "default": False, 'description': "True to indent and prettify the JSON file, False otherwise"}
    }

# ####################################################################
#
# Loader class
#
# ####################################################################


class JSONLoader(FileLoader):
    input_specs = {}
    output_specs = {'data': JSONDict}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"}
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################


class JSONDumper(FileDumper):
    input_specs = {'data': JSONDict}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": ".csv", 'description': "File format"},
        'prettify': {"type": bool, "default": False, 'description': "True to indent and prettify the JSON file, False otherwise"}
    }