# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shelve
import shutil

from gws.exception.bad_request_exception import BadRequestException
from gws.settings import Settings

# ####################################################################
#
# KVStore class
#
# ####################################################################


class KVStore:
    """
    KVStore class representing a key-value object storage engine.
    This class allows serializing/deserializing huge objects on store.
    """

    _kv_data: dict = None
    _base_dir: str = None
    _slot_path: str = None
    _file_name: str = 'data'

    def __init__(self, slot_path: str):
        super().__init__()
        while slot_path.startswith(".") or slot_path.startswith("/"):
            slot_path = slot_path.strip(".").strip("/")

        self._slot_path = slot_path

    # -- A --

    # -- D --

    def __delitem__(self, key):
        """ Delete a key """
        self._kv_data = shelve.open(self.file_path)
        if key in self._kv_data:
            val = self._kv_data[key]
            del self._kv_data[key]

        self._kv_data.close()
        return val

    @property
    def dir_path(self) -> str:
        """
        Path of directory the KVStore object

        :return: The connection path
        :rtype: str
        """

        return os.path.join(self.get_base_dir(), self._slot_path)

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

        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data.get(key)
        self._kv_data.close()
        return val

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise BadRequestException(
                f"The key must be a string. The actual value is {key}")

        if not os.path.exists(self.dir_path):
            raise BadRequestException(f"Key '{key}' does not exist")

        self._kv_data = shelve.open(self.file_path)
        val = self._kv_data[key]
        self._kv_data.close()
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

        self._kv_data = shelve.open(self.file_path)
        self._kv_data[key] = value
        self._kv_data.close()
