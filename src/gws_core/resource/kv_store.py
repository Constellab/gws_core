# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
from shelve import DbfilenameShelf
from shelve import open as shelve_open

from ..core.exception.exceptions import BadRequestException
from ..core.utils.settings import Settings
from ..resource.resource_data import ResourceData, ResourceDict

# ####################################################################
#
# KVStore class
#
# ####################################################################


class KVStore(ResourceData[ResourceDict]):
    """
    KVStore class representing a key-value object storage engine.
    This class allows serializing/deserializing huge objects on store.
    """

    _base_dir: str = None
    _slot_path: str = None
    _file_name: str = 'data'

    # For iterable, store the current index
    _iterable_index = 0

    def __init__(self, slot_path: str):
        super().__init__()
        while slot_path.startswith(".") or slot_path.startswith("/"):
            slot_path = slot_path.strip(".").strip("/")

        self._slot_path = slot_path

    # -- A --

    # -- D --

    def __delitem__(self, key):
        """ Delete a key """
        kv_data = self._open_shelve()
        if key in kv_data:
            val = kv_data[key]
            del kv_data[key]

        kv_data.close()
        return val

    @property
    def dir_path(self) -> str:
        """
        Path of directory the KVStore object

        :return: The connection path
        :rtype: str
        """

        return self.create_full_dir_path(self._slot_path)

    @classmethod
    def create_full_dir_path(cls, slot_path):
        return os.path.join(cls.get_base_dir(), slot_path)

    # -- F --

    @property
    def file_path(self) -> str:
        """
        Path of DB file the KVStore object

        :return: The connection path
        :rtype: str
        :rtype: str
        """

        return os.path.join(self.dir_path, self._file_name)

    # -- G --

    def get(self, key, default=None):
        if not isinstance(key, str):
            raise BadRequestException(
                f"The key must be a string. The actual value is {key}")

        if not os.path.exists(self.dir_path):
            return default

        kv_data = self._open_shelve()
        val = kv_data.get(key)
        kv_data.close()
        return val

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise BadRequestException(
                f"The key must be a string. The actual value is {key}")

        if not os.path.exists(self.dir_path):
            raise BadRequestException(f"Key '{key}' does not exist")

        kv_data = self._open_shelve()
        val = kv_data[key]
        kv_data.close()
        return val

    @classmethod
    def get_base_dir(cls):
        if not cls._base_dir:
            settings = Settings.retrieve()
            cls._base_dir = settings.get_kv_store_base_dir()

        return cls._base_dir

    # -- R --

    def remove(self):
        """
        Remove the store
        """

        if not os.path.exists(self.dir_path):
            return

        shutil.rmtree(self.dir_path)

    # -- S --

    def __setitem__(self, key, value):
        """
        Adds a new object value to the KVStore

        :param key: The key of the object
        :type ket: str
        :param value: The value of the object
        :type value: any
        """
        if not isinstance(key, str):
            raise BadRequestException(
                f"The key must be a string. The actual value is {key}")

        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        kv_data = self._open_shelve()
        kv_data[key] = value
        kv_data.close()

    def __next__(self):
        kv_data = self._open_shelve()

        if self._iterable_index < len(kv_data):
            value = list(kv_data.keys())[self._iterable_index]
            self._iterable_index += 1
            kv_data.close()
            return value
        else:
            kv_data.close()
            raise StopIteration

    def __iter__(self):
        self._iterable_index = 0
        return self

    def __len__(self) -> int:
        kv_data = self._open_shelve()
        length = len(kv_data)
        kv_data.close()
        return length

    def _open_shelve(self) -> DbfilenameShelf:
        return shelve_open(self.file_path)
