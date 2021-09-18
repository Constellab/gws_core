# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
import inspect
from operator import le
from shelve import DbfilenameShelf
from shelve import open as shelve_open
from time import time
from typing import Any, Dict, Callable

from ..core.exception.exceptions import BadRequestException
from ..core.utils.settings import Settings
from ..impl.file.file_helper import FileHelper

# ####################################################################
#
# KVStore class
#
# ####################################################################


class KVStore(Dict[str, Any]):
    """
    KVStore class representing a key-value object storage engine.
    This class allows serializing/deserializing huge objects on store.
    """

    # When true the KVStore can't be update (but read), it a modification happens, it
    # copies the file before updating the data
    # It create a copy of the current file to _lock_copy_file_path
    _lock: bool = False
    _lock_copy_full_file_path: str = None

    _full_file_path: str

    # For iterable, store the current index
    _iterable_index = 0

    # class level
    _base_dir: str = None

    def __init__(self, full_file_path: str):
        super().__init__()
        self._full_file_path = full_file_path

    def __contains__(self, key) -> int:
        kv_data = self._open_shelve()
        return kv_data.__contains__(key)
    
    @property
    def full_file_dir(self) -> str:
        """
        Path of DB file the KVStore object

        :return: The connectiotn path
        :rtype: str
        :rtype: str
        """

        return os.path.dirname(self.full_file_path)

    @property
    def full_file_path(self) -> str:
        """
        Path of DB file the KVStore object

        :return: The connectiotn path
        :rtype: str
        :rtype: str
        """

        return self._full_file_path + '.db'

    def get_full_path_without_extension(self) -> str:
        return self._full_file_path
    
    # -- G --

    def get(self, key, default=None):
        self._check_key(key)

        kv_data = self._open_shelve()
        val = kv_data.get(key, default=default)
        kv_data.close()
        return val

    def __getitem__(self, key):
        self._check_key(key)

        kv_data = self._open_shelve()
        val = kv_data[key]
        kv_data.close()
        return val

    # -- R --

    def remove(self):
        """
        Remove the store
        """

        if self.file_exists():
            return
        # os.remove(self.full_file_path)
        os.remove(self.full_file_dir)

    # -- S --

    def dump(self, key, obj: Any, dump_func: Callable=None, *args, **kwargs):
        """ 
            Serialize and dump any object in the store 

            * If `dump_func` is `None`, it is serialized and dumped using python `Pickle` functionalities.
            * If `dump_func` is callable, it is used to dump the `obj`.
              In this case, the `dump_func` function must be `dump_func(obj, path, *args, **kwargs)`
              The `args` and `kwargs` parmeters are passed to the `dump_func`
              For exemple:
              -----------
              For complex object dumps, the `gws_core.Utils.Serializer.dump()` method could be used.

            :param key: The key in the store
            :type param: `str`
            :param obj: The object to dump in the store
            :type obj: `any`
            :param dump_func: The user function to use to serialize the object
            :type dump_func: `Callable`
        """

        if inspect.isfunction(dump_func):
            if not os.path.exists(self.full_file_dir):
                os.makedirs(self.full_file_dir)

            path = os.path.join(self.full_file_dir, key+'.dump')
            dump_func(obj, path, *args, **kwargs)
            self[key] = path
        else:
            self[key] = obj

    def load(self, key, load_func: Callable=None, *args, **kwargs) -> Any:
        """ 
            Seserialize and load any object in the store

            * If `load_func` is `None`, it is deserialized and loaded using python `Pickle` functionalities.
            * If `load_func` is callable, it is used to load the `obj`.
              In this case, the `load_func` function must have be `obj = load_func(path: str, *args, **kwargs)`
              The `args` and `kwargs` parmeters are passed to the `load_func`
              For exemple:
              -----------
              For complex object loading, the `gws_core.Utils.Serializer.load()` method could be used.

            :param key: The key in the store
            :type param: `str`
            :param load_func: The user function to use to deserialize the object
            :type load_func: `Callable`
            :return: The loaded object
            :rtype: `any`
        """

        if inspect.isfunction(load_func):
            path = self[key]
            data = load_func(path, *args, **kwargs)
            return data
        else:
            return self[key]

    def __setitem__(self, key, value):
        """
        Adds a new object value to the KVStore

        :param key: The key of the object
        :type ket: str
        :param value: The value of the object
        :type value: any
        """
        self.check_before_write(key)

        kv_data = self._open_shelve()
        kv_data[key] = value
        kv_data.close()

    def __delitem__(self, key):
        self.check_before_write(key)

        """ Delete a key """
        kv_data = self._open_shelve()
        if key in kv_data:
            val = kv_data[key]
            del kv_data[key]

        kv_data.close()
        return val

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
        # if not FileHelper.exists_on_os(self.get_base_dir()):
        #     os.mkdir(self.get_base_dir())
        if not FileHelper.exists_on_os(self.full_file_dir):
            os.makedirs(self.full_file_dir)

        return shelve_open(self.get_full_path_without_extension())

    def check_before_write(self, key: str) -> None:
        self._check_key(key=key)
        if self._lock:
            self._copy_file(self._lock_copy_full_file_path)
            self._unlock()

    def check_before_read(self) -> None:
        if not self.file_exists():
            self._copy_file(self._lock_copy_full_file_path)
            self._unlock()

    def _unlock(self) -> None:
        """Remove lock and update file path,
        """
        self._lock = False
        self._full_file_path = self._lock_copy_full_file_path
        self._lock_copy_full_file_path = None

    def _copy_file(self, destination_path: str) -> None:
        src_dir = self.full_file_dir
        dest_dir = os.path.dirname(self.get_full_file_path(destination_path))
        shutil.copytree(src_dir, dest_dir)
        # shutil.copyfile(self.full_file_path, self.get_full_file_path(destination_path))

    def file_exists(self) -> bool:
        return FileHelper.exists_on_os(self.full_file_path)

    def lock(self, _lock_copy_file_path: str) -> None:
        """ Lock the kv store, it can no longer be modified. If a modification happens, it
            copies the file before updating the data, To copy the file is uses the _lock_copy_name

        :return: [description]
        :rtype: [type]
        """
        self._lock_copy_full_file_path = _lock_copy_file_path
        self._lock = True

    def _check_key(self, key: str) -> None:
        if not isinstance(key, str):
            raise BadRequestException(
                f"The key must be a string. The actual value is {key}")

    ################################# Class methods ################################

    @classmethod
    def get_base_dir(cls) -> str:
        if not cls._base_dir:
            settings = Settings.retrieve()
            cls._base_dir = settings.get_kv_store_base_dir()

        return cls._base_dir

    @classmethod
    def get_full_file_path(cls, file_name: str, with_extension: bool = True) -> str:
        full_path: str = os.path.join(cls.get_base_dir(), file_name, "store")
        if with_extension:
            full_path += '.db'

        return full_path

    @classmethod
    def from_filename(cls, file_name: str) -> 'KVStore':
        return KVStore(cls.get_full_file_path(file_name=file_name, with_extension=False))

    @classmethod
    def empty(cls) -> 'KVStore':
        """Create an new kv store and generate the file name automatically

        :return: [description]
        :rtype: [type]
        """
        generated_file_name: str = str(time()).replace('.', '')
        return KVStore(cls.get_full_file_path(file_name=generated_file_name, with_extension=False))
