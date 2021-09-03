# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import os
import shutil
from io import IOBase
from pathlib import Path
from tempfile import SpooledTemporaryFile
from time import time
from typing import List, Union

from ...core.decorator.transaction import transaction
from ...core.exception.exceptions import BadRequestException
from ...core.utils.settings import Settings
from .file import File
from .file_helper import FileHelper
from .file_resource import FileResource
from .file_store import FileStore


class LocalFileStore(FileStore):
    title = "Local file store"
    description = "Storage engine to locally store files"
    _base_dir: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.path:
            self.data["path"] = os.path.join(self.get_base_dir(), self.uri)

    def add_from_path(self, source_file: str, dest_file_name: str = None) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `str` (file path),
        :return: The file object
        :rtype: gws.file.File.
        """

        file = self.create_file(file_name=dest_file_name)
        self._copy_file(source_file, file.path)

        return file

    def add_from_file(self, source_file: File, dest_file_name: str = None) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `File`
        :return: The file object
        :rtype: gws.file.File.
        """

        if self.contains(source_file):
            return source_file
        return self.add_from_path(source_file=source_file.path, dest_file_name=dest_file_name)

    def add_from_temp_file(self, source_file: Union[IOBase, SpooledTemporaryFile], dest_file_name: str = None) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `IOBase` or `SpooledTemporaryFile`
        :return: The file object
        :rtype: gws.file.File.
        """

        file = self.create_file(file_name=dest_file_name)
        self._init_dir(file.dir)

        with open(file.path, "wb") as buffer:
            shutil.copyfileobj(source_file, buffer)

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

    def _init_dir(self, dir: str) -> None:
        """Create the directory if it doesn't exist
        """
        # copy disk file
        if not os.path.exists(dir):
            os.makedirs(dir)
            if not os.path.exists(dir):
                raise BadRequestException(f"Cannot create directory '{dir}'")

    def create_file(self, file_type: type = None, file_name: str = None) -> File:
        file: File
        if isinstance(file_type, type):
            file = file_type()
        else:
            file = File()
        file.path = self._get_new_file_path(file_name)
        file.file_store_uri = self.uri

        return file

    def _get_new_file_path(self, dest_file_name: str = None) -> str:
        """Generate a new file name

        :param dest_file_name: [description], defaults to None
        :type dest_file_name: str, optional
        :return: [description]
        :rtype: str
        """
        # if there is no file dest, generate a name
        if dest_file_name is None:
            time_file_name: str = str(time()).replace('.', '')
            return os.path.join(self.path, time_file_name)

        #  create the file if another doesn't exists
        if not self.file_exists(dest_file_name):
            return os.path.join(self.path, dest_file_name)

        extension: str = FileHelper.get_extension(dest_file_name)
        file_name: str = FileHelper.get_name(dest_file_name)

        # If the file exists, find a unique name with a number
        unique: int = 1
        while self.file_exists(f"{file_name}_{unique}{extension}"):
            unique += 1
        return os.path.join(self.path, f"{file_name}_{unique}{extension}")

    def contains(self, file: File) -> bool:
        return self.path in file.path

    # -- D --

    @classmethod
    def drop_table(cls):
        cls.remove_all_files()
        super().drop_table()

    def delete_instance(self):
        if FileResource.table_exists():
            FileResource.delete().where(FileResource.file_store_uri == self.uri).execute()
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        super().delete_instance()

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
    def get_base_dir(cls):
        if not cls._base_dir:
            settings = Settings.retrieve()
            cls._base_dir = settings.get_file_store_dir()
        return cls._base_dir

    # -- R --

    @classmethod
    @transaction()
    def remove_all_files(cls):
        """
        Remove all the files from the FileStore
        """

        settings = Settings.retrieve()
        if not settings.is_dev and not settings.is_test:
            raise BadRequestException("Only allowed in dev and test mode")
        files: List[FileStore] = cls.select()
        for file_store in files:
            file_store.delete_instance()

    def file_exists(self, file_name: str) -> bool:
        return os.path.exists(os.path.join(self.path, file_name))
