import json
from typing import Any

from gws_core.resource.resource import Resource
from gws_core.resource.resource_serialized import ResourceSerialized

from ...core.model.model import Model
from ...resource.resource_decorator import ResourceDecorator


@ResourceDecorator("JSONDict")
class JSONDict(Resource):

    # -- A --

    data: dict

    def serialize(self) -> ResourceSerialized:
        return ResourceSerialized(light_data=self.data)

    def deserialize(self, resource_serialized: ResourceSerialized) -> None:
        self.data = resource_serialized.light_data

    def export(self, file_path: str, file_format: str = ".json", prettify: bool = False):
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        with open(file_path, "w") as f:
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
    def import_resource(cls, file_path: str, file_format: str = ".json") -> Any:
        """
        Import a give from repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        with open(file_path, "r") as f:
            json_data = cls()
            json_data.data = json.load(f)

        return json_data

    # -- J --

    @classmethod
    def join(cls, *args, **params) -> Model:
        """
        Join several resources

        :param params: Joining parameters
        :type params: dict
        """

        # @ToDo: ensure that this method is only called by an Joiner

        pass

    # -- K --

    # -- S --

    def select(self, **params) -> Model:
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
