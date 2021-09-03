# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import Any, Type

from ...core.exception.exceptions import BadRequestException
from ...impl.file.file_helper import FileHelper
from ...resource.resource import Resource, SerializedResourceData
from ...resource.resource_decorator import resource_decorator
from ...resource.resource_set import ResourceSet


@resource_decorator("File")
class File(Resource):
    """
    File class
    """

    path: str
    file_store_uri: str
    _mode = "t"
    _table_name = "gws_file"

    def __init__(self, *args, **kwargs):
        self.path = ""
        self.file_store_uri = ""
        super().__init__(*args, **kwargs)

    def serialize_data(self) -> SerializedResourceData:
        return {
            "path": self.path,
            "file_store_uri": self.file_store_uri
        }

    def deserialize_data(self, data: SerializedResourceData) -> None:
        if data:
            self.path = data['path']
            self.file_store_uri = data['file_store_uri']

    @property
    def dir(self):
        return FileHelper.get_dir(self.path)

    # -- E --

    @property
    def extension(self):
        return FileHelper.get_extension(self.path)

    def _exists(self):
        return os.path.exists(self.path)

    # -- F --

    # -- I --

    def is_json(self):
        return FileHelper.is_json(self.path)

    def is_csv(self):
        return FileHelper.is_csv(self.path)

    def is_txt(self):
        return FileHelper.is_txt(self.path)

    def is_jpg(self):
        return FileHelper.is_jpg(self.path)

    def is_png(self):
        return FileHelper.is_png(self.path)

    # -- M --

    @property
    def mime(self):
        return FileHelper.get_mime(self.path)

    @property
    def name(self):
        return FileHelper.get_name_with_extension(self.path)

    # -- O --

    def open(self, mode: str):
        """
        Open the file
        """

        if self._exists():
            return open(self.path, mode)
        else:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)
                if not os.path.exists(self.dir):
                    raise BadRequestException(
                        f"Cannot create directory {self.dir}")
            return open(self.path, mode="w+")

    # -- P --

    # -- R --

    def read(self):
        m = "r+"+self._mode
        with self.open(m) as fp:
            data = fp.read()
        return data

    def readline(self):
        m = "r+"+self._mode
        with self.open(m) as fp:
            data = fp.readline()
        return data

    def readlines(self, n=-1):
        m = "r+"+self._mode
        with self.open(m) as fp:
            data = fp.readlines(n)
        return data

    # -- T --

    def to_json(self) -> dict:
        _json = {}

        _json["path"] = self.path
        return _json

    # -- W --

    def write(self, data: str, discard=False):
        """
        Write in the file
        """
        m = "a+"+self._mode
        with self.open(m) as fp:
            fp.write(data)

    @classmethod
    def get_resource_model_type(cls) -> Type[Any]:
        """Return the resource model associated with this Resource
        //!\\ To overwrite only when you know what you are doing

        :return: [description]
        :rtype: Type[Any]
        """
        from .file_resource_model import FileResourceModel
        return FileResourceModel

    # -- S --

# ####################################################################
#
# FileSet class
#
# ####################################################################


class FileSet(ResourceSet):
    _resource_types = (File, )
