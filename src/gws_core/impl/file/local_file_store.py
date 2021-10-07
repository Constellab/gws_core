# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import os
import shutil
from inspect import isclass
from io import IOBase
from pathlib import Path
from tempfile import SpooledTemporaryFile
from time import time
from typing import List, Type, Union

from ...core.decorator.transaction import transaction
from ...core.exception.exceptions import BadRequestException
from ...core.utils.settings import Settings
from .file import File
from .file_helper import FileHelper
from .file_store import FileStore


class LocalFileStore(FileStore):
    title = "Local file store"
    description = "Storage engine to locally store files"
    _base_dir: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.path:
            self.data["path"] = os.path.join(self.get_base_dir(), self.uri)

    def add_from_path(self, source_file_path: str, dest_file_name: str = None, file_type: Type[File] = File) -> File:
        """
        Add a file from an external repository to a local store.

        :param source_file: The source file
        :type source_file: `str` (file path),
        :return: The file object
        :rtype: gws.file.File.
        """
        if dest_file_name is None:
            dest_file_name = FileHelper.get_name_with_extension(source_file_path)

        file = self._init_file(file_name=dest_file_name, file_type=file_type)
        self._copy_file(source_file_path, file.path)

        return file

    def add_from_temp_file(
            self, source_file: Union[IOBase, SpooledTemporaryFile],
            dest_file_name: str = None, file_type: Type[File] = File) -> File:
        """
        Add a file from an external repository to a local store.

        :param source_file: The source file
        :type source_file: `IOBase` or `SpooledTemporaryFile`
        :return: The file object
        :rtype: gws.file.File.
        """

        file = self._init_file(file_name=dest_file_name, file_type=file_type)
        self._init_dir(file.dir)

        with open(file.path, "wb") as buffer:
            shutil.copyfileobj(source_file, buffer)

        return file

    def create_empty(self, file_name: str = None, file_type: Type[File] = File) -> File:
        file: File = self._init_file(file_name=file_name, file_type=file_type)

        self._init_dir(file.dir)

        open(file.path, 'a').close()
        return file

    def _copy_file(self, source: str, destination: str) -> None:
        """Copy a file from a path to another path

        :param source: [description]
        :type source: str
        :param destination: [description]
        :type destination: str
        """
        self._init_dir(str(Path(destination).parent))
        shutil.copy2(source, destination)

    # -- B --

    # -- C --

    def _init_dir(self, dir_: str) -> None:
        """Create the directory if it doesn't exist
        """
        # copy disk file
        if not os.path.exists(dir_):
            os.makedirs(dir_)
            if not os.path.exists(dir_):
                raise BadRequestException(f"Cannot create directory '{dir_}'")

    def _init_file(self, file_name: str = None, file_type: Type[File] = File) -> File:

        if not isclass(file_type) or not issubclass(file_type, File):
            raise BadRequestException(f"The file type '{str(file_type)}' is not a File class")

        file: File = file_type()
        file.path = self.get_new_file_path(file_name)
        file.file_store_uri = self.uri

        return file

    def get_new_file_path(self, dest_file_name: str = None) -> str:
        """Generate the file path from file name and avoid duplicate

        :param dest_file_name: [description], defaults to None
        :type dest_file_name: str, optional
        :return: [description]
        :rtype: str
        """
        # if there is no file dest, generate a name
        if dest_file_name is None or len(dest_file_name) == 0:
            time_file_name: str = str(time()).replace('.', '')
            return os.path.join(self.path, time_file_name)

        #  create the file if another doesn't exists
        if not self.file_name_exists(dest_file_name):
            return os.path.join(self.path, dest_file_name)

        extension: str = FileHelper.get_extension(dest_file_name)
        file_name: str = FileHelper.get_name(dest_file_name)

        # If the file exists, find a unique name with a number
        unique: int = 1
        while self.file_name_exists(f"{file_name}_{unique}{extension}"):
            unique += 1
        return os.path.join(self.path, f"{file_name}_{unique}{extension}")

    def file_path_exists(self, file_path: str) -> bool:
        # clean the file path
        file_path = str(Path(file_path))

        # Check that the file path is in the file store
        if not file_path.startswith(self.get_base_dir()):
            return False

        return os.path.exists(file_path)

    def _file_get_path_from_file_name(self, file_name: str) -> str:
        return os.path.join(self.path, file_name)

    # -- D --

    @classmethod
    def drop_table(cls, *args, **kwargs):
        cls.remove_all_file_stores()
        super().drop_table(*args, **kwargs)

    # -- E --

    # -- G --

    @classmethod
    def get_default_instance(cls) -> 'LocalFileStore':
        try:
            file_store: FileStore = cls.get_by_id(1)
        except Exception:
            file_store = cls()
            file_store.save()
        return file_store

    # -- I --

    # -- M --

    # -- P --

    @property
    def path(self) -> str:
        """
        Get path of the local file store
        """

        return super().path

    # -- F --

    @path.setter
    def path(self, path: str) -> None:
        """
        Locked method.
        The path of a LocalFileStore is automatically computed and cannot be manually altered.
        """

        raise BadRequestException("Cannot manually set LocalFileStore path")

    # -- G --

    @classmethod
    def get_base_dir(cls) -> str:
        if not cls._base_dir:
            settings = Settings.retrieve()
            cls._base_dir = settings.get_file_store_dir()
        return str(Path(cls._base_dir))

    # -- R --

    @classmethod
    @transaction()
    def remove_all_file_stores(cls):
        """
        Remove all the files from the FileStore
        """

        settings = Settings.retrieve()
        if not settings.is_dev and not settings.is_test:
            raise BadRequestException("Only allowed in dev and test mode")
        file_store_list: List[FileStore] = cls.select()
        for file_store in file_store_list:
            file_store.delete_instance()
