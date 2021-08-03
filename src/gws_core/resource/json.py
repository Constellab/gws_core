# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from ..core.model.model import Model
from .file.file import File
from .file.file_uploader import (FileDumper, FileExporter, FileImporter,
                                 FileLoader)
from .resource import Resource


class JSONDict(Resource):

    # -- A --

    # -- E --

    def _export(self, file_path: str, file_format: str = ".json", prettify: bool = False):
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        with open(file_path, "w") as f:
            if prettify:
                json.dump(self.kv_data, f, indent=4)
            else:
                json.dump(self.kv_data, f)

    # -- G --

    def __getitem__(self, key):
        return self.kv_data[key]

    def get(self, key, default=None):
        return self.kv_data.get(key, default)

    # -- I --

    @classmethod
    def _import(cls, file_path: str, file_format: str = ".json") -> any:
        """
        Import a give from repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        with open(file_path, "r") as f:
            json_data = cls()
            json_data.kv_data = json.load(f)

        return json_data

    # -- J --

    @classmethod
    def _join(cls, *args, **params) -> Model:
        """
        Join several resources

        :param params: Joining parameters
        :type params: dict
        """

        # @ToDo: ensure that this method is only called by an Joiner

        pass

    # -- K --

    @property
    def kv_data(self):
        if not 'kv_data' in self.data:
            self.data["kv_data"] = {}

        return self.data["kv_data"]

    @kv_data.setter
    def kv_data(self, kv_data: dict):
        self.data["kv_data"] = kv_data

    # -- S --

    def _select(self, **params) -> Model:
        """
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """

        # @ToDo: ensure that this method is only called by an Selector

        pass

    def __setitem__(self, key, val):
        self.data[key] = val

    # -- T --

    def to_json(self, stringify: bool = False, prettify: bool = False, **kwargs):
        _json = super().to_json(**kwargs)
        _json["data"]["content"] = self.kv_data

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

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
