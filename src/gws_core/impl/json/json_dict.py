# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Any

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...config.config_types import ConfigParams
from ...config.param_spec import BoolParam, StrParam
from ...impl.file.file import File
from ...resource.r_field import DictRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...task.exporter import export_to_path
from ...task.importer import import_from_path


@resource_decorator("JSONDict")
class JSONDict(Resource):

    data: dict = DictRField()

    def __init__(self, data: dict = None):
        super().__init__()
        if data is None:
            data = {}
        else:
            if not isinstance(data, dict):
                raise BadRequestException("The data must be an instance of dict")
        self.data = data

    @export_to_path(specs={
        'file_name': StrParam(default_value='file.json', short_description="Destination file name in the store"),
        'file_format': StrParam(default_value=".json", short_description="File format"),
        'prettify': BoolParam(default_value=False, short_description="True to indent and prettify the JSON file, False otherwise")
    })
    def export_to_path(self, dest_dir: str, params: ConfigParams) -> File:
        """
        Export to a give repository

        :param dest_dir: The destination directory
        :type dest_dir: str
        """
        file_path = os.path.join(dest_dir, params.get_value('file_name', 'file.json'))

        with open(file_path, "w", encoding="utf-8") as f:
            if params.get_value('prettify', False):
                json.dump(self.data, f, indent=4)
            else:
                json.dump(self.data, f)

        return File(file_path)

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    @classmethod
    @import_from_path(specs={'file_format': StrParam(default_value=".json", short_description="File format")})
    def import_from_path(cls, file: File, params: ConfigParams) -> Any:
        """
        Import a give from repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        with open(file.path, "r", encoding="utf-8") as f:
            json_data = cls()
            json_data.data = json.load(f)

        return json_data

    def __setitem__(self, key, val):
        self.data[key] = val
