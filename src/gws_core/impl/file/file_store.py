# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import io
import os
import shutil
import tempfile
from abc import abstractclassmethod, abstractmethod
from pathlib import Path
from typing import List, Union

from ...core.decorator.transaction import Transaction
from ...core.exception.exceptions import BadRequestException
from ...core.model.model import Model
from ...core.utils.settings import Settings
from ...model.typing_register_decorator import TypingDecorator
from .file import File
from .file_resource import FileResource

# ####################################################################
#
# FileStore class
#
# ####################################################################


@TypingDecorator(unique_name="FileStore", object_type="GWS_CORE", hide=True)
class FileStore(Model):
    """
    FileStore class
    """
    title = "File store"
    description = ""
    _table_name = "gws_file_store"

    # -- A --
    @abstractmethod
    def add(self, source_file: Union[str, io.IOBase, tempfile.SpooledTemporaryFile, File]) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `str` (file path), `gws.file.File`, `io.IOBase` or `tempfile.SpooledTemporaryFile`
        :param dest_file_name: The destination file name
        :type dest_file_name: `str`
        :return: The file object
        :rtype: gws.file.File.
        """

        raise BadRequestException('Not implemented')

    # -- O --

    @classmethod
    @abstractclassmethod
    def open(cls, file, mode):
        """
        Open a file. Must be implemented by the child class.

        :param file: The file to open
        :type file: `gws.file.File`
        :param mode: Mode (see native Python `open` function)
        :type mode: `str`
        :return: The file object
        :rtype: Python `file-like-object` or `stream`.
        """

        raise BadRequestException('Not implemented')

    # -- P --

    @property
    def path(self) -> str:
        """
        Get path (or url) of the store
        """

        return self.data.get("path", "")

    # -- F --

    @path.setter
    def path(self, path: str) -> str:
        """
        Set the path (or url) of the store
        """

        self.data["path"] = path

# ####################################################################
#
# LocalFileStore class
#
# ####################################################################


class LocalFileStore(FileStore):
    title = "Local file store"
    description = "Storage engine to locally store files"
    _base_dir: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.path:
            self.data["path"] = os.path.join(self.get_base_dir(), self.uri)

    # -- A --
    # TODO to test
    def add(self, source_file: Union[str, io.IOBase, tempfile.SpooledTemporaryFile, File],
            dest_file_name: str = "") -> File:
        """
        Add a file from an external repository to a local store

        :param source_file: The source file
        :type source_file: `str` (file path), `gws.file.File`, `io.IOBase` or `tempfile.SpooledTemporaryFile`
        :param dest_file_name: The destination file name
        :type dest_file_name: `str`
        :return: The file object
        :rtype: gws.file.File.
        """

        if not self.is_saved():
            self.save()
        with self._db_manager.db.atomic() as transaction:
            try:
                # create DB file object
                if isinstance(source_file, File):
                    if self.contains(source_file):
                        return source_file
                    file: File = source_file
                    source_file_path = file.path
                    if not dest_file_name:
                        dest_file_name = Path(source_file_path).name
                    file.path = self._get_file_path(name=dest_file_name)
                else:
                    if not dest_file_name:
                        if isinstance(source_file, str):
                            dest_file_name = Path(source_file).name
                        else:
                            dest_file_name = "file"

                    file = self.create_file(name=dest_file_name)
                    source_file_path = source_file
                # copy disk file
                if not os.path.exists(file.dir):
                    os.makedirs(file.dir)
                    if not os.path.exists(file.dir):
                        raise BadRequestException(
                            f"Cannot create directory '{file.dir}'")
                if isinstance(source_file, (io.IOBase, tempfile.SpooledTemporaryFile, )):
                    with open(file.path, "wb") as buffer:
                        shutil.copyfileobj(source_file, buffer)
                else:
                    shutil.copy2(source_file_path, file.path)

                return file
            except Exception as err:
                transaction.rollback()
                raise BadRequestException(
                    f"An error occured. Error: {err}") from err

    # -- B --

    # -- C --

    def _get_file_path(self, name: str = "") -> str:
        return os.path.join(self.path, self.uri, name)

    def create_file(self, name: str, file_type: type = None) -> File:
        file: File
        if isinstance(file_type, type):
            file = file_type()
        else:
            file = File()
        file.path = self._get_file_path(name)
        file.file_store_uri = self.uri

        return file

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
    def get_default_instance(cls) -> 'FileStore':
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
    def path(self, path: str) -> str:
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

    def remove(self, file: File):
        """
        Remove a file from the FileStore
        """

        if self.contains(file):
            file.delete_instance()
        else:
            raise BadRequestException(
                f"File '{file.uri}' is not in the file_store '{self.uri}'")

    @classmethod
    @Transaction()
    def remove_all_files(cls):
        """
        Remove all the files from the FileStore
        """

        settings = Settings.retrieve()
        if not settings.is_dev and not settings.is_test:
            raise BadRequestException("Only allowed in dev and test mode")
        files: List[FileStore] = cls.select()
        for fs in files:
            fs.delete_instance()
