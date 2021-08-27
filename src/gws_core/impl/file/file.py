# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

import mimetypes
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Type

from ...core.exception.exceptions import BadRequestException
from ...resource.resource import Resource
from ...resource.resource_decorator import ResourceDecorator
from ...resource.resource_set import ResourceSet

if TYPE_CHECKING:
    from .file_store import FileStore


@ResourceDecorator("File")
class File(Resource):
    """
    File class
    """

    path = str
    file_store_uri = str
    _mode = "t"
    _table_name = "gws_file"

    # -- D --
    def delete_resource(self,):
        shutil.rmtree(self.path)

    @property
    def dir(self):
        return Path(self.path).parent

    # -- E --

    @property
    def extension(self):
        return Path(self.path).suffix

    def exists(self):
        return os.path.exists(self.path)

    # -- F --

    # -- I --

    def is_json(self):
        return self.extension in [".json"]

    def is_csv(self):
        return self.extension in [".csv", ".tsv"]

    def is_txt(self):
        return self.extension in [".txt"]

    def is_jpg(self):
        return self.extension in [".jpg", ".jpeg"]

    def is_png(self):
        return self.extension in [".png"]

    # -- M --

    @property
    def mime(self):
        ext = self.extension
        if ext:
            return mimetypes.types_map[self.extension]
        else:
            return None

    def move_to_store(self, fs: 'FileStore'):
        if not fs.contains(self):
            fs.add(self)

    def move_to_default_store(self):
        from .file_store import LocalFileStore
        fs = LocalFileStore.get_default_instance()
        if not fs.contains(self):
            fs.add(self)

    # -- N --

    @property
    def name(self):
        return Path(self.path).name

    # -- O --

    def open(self, mode: str):
        """
        Open the file
        """

        if self.exists():
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

    def get_resource_model_type(cls) -> Type[Any]:
        """Return the resource model associated with this Resource
        //!\\ To overwrite only when you know what you are doing

        :return: [description]
        :rtype: Type[Any]
        """
        from .file_resource import FileResource
        return FileResource

    # -- S --

# ####################################################################
#
# FileSet class
#
# ####################################################################


class FileSet(ResourceSet):
    _resource_types = (File, )
