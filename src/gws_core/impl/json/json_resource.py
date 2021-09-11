# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Any
from copy import deepcopy

from ...core.model.model import Model
from ...resource.resource import Resource, SerializedResourceData
from ...resource.resource_decorator import resource_decorator

@resource_decorator("JSONDict")
class JSONDict(Resource):

    data: dict = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data is None:
            self.data = {}

    def serialize_data(self) -> SerializedResourceData:
        return self.data

    def deserialize_data(self, data: SerializedResourceData) -> None:
        self.data = deepcopy(data)

    # -- E --

    def export(self, file_path: str, file_format: str = ".json", prettify: bool = False):
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        with open(file_path, "w", encoding="utf-8") as f:
            if prettify:
                json.dump(self.data, f, indent=4)
            else:
                json.dump(self.data, f)

    # -- G --

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    # -- I --

    @classmethod
    def import_from_path(cls, file_path: str, file_format: str = ".json") -> Any:
        """
        Import a give from repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        with open(file_path, "r", encoding="utf-8") as f:
            json_data = cls()
            json_data.data = json.load(f)

        return json_data

    # -- J --

    # -- K --

    # -- S --

    def __setitem__(self, key, val):
        self.data[key] = val

    # -- T --
