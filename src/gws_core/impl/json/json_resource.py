import json

from ...core.model.model import Model
from ...resource.resource import Resource


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
