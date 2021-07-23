# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import io
import os
import shutil
import tempfile
from pathlib import Path

from gws.exception.bad_request_exception import BadRequestException

from .db.model import Model
from .settings import Settings

# ####################################################################
#
# FileStore class
#
# ####################################################################


class FileStore(Model):
    """
    FileStore class
    """

    title = "File store"
    description = ""
    _table_name = "gws_file_store"

    # -- A --

    def add(self, source_file: (str, io.IOBase, tempfile.SpooledTemporaryFile, 'File', )):
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
            self.save()

    # -- A --

    def add(self, source_file: (str, io.IOBase, tempfile.SpooledTemporaryFile, 'File', ), dest_file_name: str = ""):
        """
        Add a file from an external repository to a local store

        :param source_file: The source file
        :type source_file: `str` (file path), `gws.file.File`, `io.IOBase` or `tempfile.SpooledTemporaryFile`
        :param dest_file_name: The destination file name
        :type dest_file_name: `str`
        :return: The file object
        :rtype: gws.file.File.
        """

        from .file import File
        if not self.is_saved():
            self.save()
        with self._db_manager.db.atomic() as transaction:
            try:
                # create DB file object
                if isinstance(source_file, File):
                    if self.contains(source_file):
                        return source_file
                    f = source_file
                    source_file_path = f.path
                    if not dest_file_name:
                        dest_file_name = Path(source_file_path).name
                    f.path = self.__create_valid_file_path(
                        f, name=dest_file_name)
                else:
                    if not dest_file_name:
                        if isinstance(source_file, str):
                            dest_file_name = Path(source_file).name
                        else:
                            dest_file_name = "file"

                    f = self.create_file(name=dest_file_name)
                    source_file_path = source_file
                # copy disk file
                if not os.path.exists(f.dir):
                    os.makedirs(f.dir)
                    if not os.path.exists(f.dir):
                        raise Exception("FileStore", "add",
                                        f"Cannot create directory '{f.dir}'")
                if isinstance(source_file, (io.IOBase, tempfile.SpooledTemporaryFile, )):
                    with open(f.path, "wb") as buffer:
                        shutil.copyfileobj(source_file, buffer)
                else:
                    shutil.copy2(source_file_path, f.path)
                # save DB file object
                f.file_store_uri = self.uri
                f.save()
                return f
            except Exception as err:
                transaction.rollback()
                raise BadRequestException(
                    f"An error occured. Error: {err}") from err

    # -- B --

    # -- C --

    def __create_valid_file_path(self, file: 'File', name: str = ""):
        if not file.uri:
            file.save()
        file.path = os.path.join(self.path, file.uri, name)
        file.save()
        return file.path

    def create_file(self, name: str, file_type: type = None):
        from .file import File
        if isinstance(file_type, type):
            file = file_type()
        else:
            file = File()
        self.__create_valid_file_path(file, name)
        file.save()
        return file

    def contains(self, file: 'File') -> bool:
        return self.path in file.path

    # -- D --

    @classmethod
    def drop_table(cls):
        cls.remove_all_files()
        super().drop_table()

    def delete_instance(self):
        from .file import File
        if File.table_exists():
            File.delete().where(File.file_store_uri == self.uri).execute()
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        super().delete_instance()

    # -- E --

    # -- G --

    @classmethod
    def get_default_instance(cls):
        try:
            fs = cls.get_by_id(1)
        except Exception as _:
            fs = cls()
            fs.save()
        return fs

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

    def remove(self, file: 'File'):
        """
        Remove a file from the FileStore
        """

        if self.contains(file):
            file.delete_instance()
        else:
            raise BadRequestException(
                f"File '{file.uri}' is not in the file_store '{self.uri}'")

    @classmethod
    def remove_all_files(cls):
        """
        Remove all the files from the FileStore
        """

        settings = Settings.retrieve()
        if not settings.is_dev and not settings.is_test:
            raise BadRequestException("Only allowed in dev and test mode")
        with cls._db_manager.db.atomic():
            Q = cls.select()
            for fs in Q:
                fs.delete_instance()
