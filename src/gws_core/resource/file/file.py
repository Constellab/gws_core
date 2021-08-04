# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import mimetypes
import os
import shutil
from pathlib import Path

from peewee import CharField

from ...core.exception.exceptions import BadRequestException
from ...core.utils.settings import Settings
from ..resource import Resource
from ..resource_set import ResourceSet
from .file_store import FileStore, LocalFileStore


class File(Resource):
    """
    File class
    """

    file_store_uri = CharField(null=True, index=True)
    path = CharField(null=True, index=True, unique=True)
    _mode = "t"
    _table_name = "gws_file"
    __DOWNLOAD_URL = "https://lab.{}/core-api/file/{}/{}/download"

    # -- D --

    def delete_instance(self, *args, **kwargs):
        with self._db_manager.db.atomic():
            status = super().delete_instance(*args, **kwargs)
            if status:
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

    @property
    def file_store(self):
        if self.file_store_uri:
            fs = FileStore.get(FileStore.uri == self.file_store_uri).cast()
        else:
            try:
                fs = LocalFileStore.get_by_id(0)
            except:
                # create a default LocalFileStore
                fs = LocalFileStore()
                fs.save()
            self.file_store_uri = fs.uri
            self.save()

        return fs

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

    def to_json(self, stringify: bool = False, prettify: bool = False, shallow: bool = True, **kwargs):
        _json = super().to_json(**kwargs)
        settings = Settings.retrieve()
        host = settings.data.get("host", "0.0.0.0")
        vhost = settings.data.get("virtual_host", host)
        _json["url"] = File.__DOWNLOAD_URL.format(vhost, self.type, self.uri)

        if not shallow:
            if self.is_json():
                _json["data"]["content"] = json.loads(self.read())
            else:
                _json["data"]["content"] = self.read()
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    # -- W --

    def write(self, data: str, discard=False):
        """
        Write in the file
        """
        m = "a+"+self._mode
        with self.open(m) as fp:
            fp.write(data)

    # -- S --

# ####################################################################
#
# FileSet class
#
# ####################################################################


class FileSet(ResourceSet):
    _resource_types = (File, )
