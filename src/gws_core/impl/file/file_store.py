# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractclassmethod, abstractmethod
from io import IOBase
from tempfile import SpooledTemporaryFile
from typing import Type, Union

from ...core.exception.exceptions import BadRequestException
from ...core.model.model import Model
from ...model.typing_register_decorator import typing_registrator
from .file import File

# ####################################################################
#
# FileStore class
#
# ####################################################################


@typing_registrator(unique_name="FileStore", object_type="MODEL", hide=True)
class FileStore(Model):
    """
    FileStore class
    """
    title = "File store"
    description = ""
    _table_name = "gws_file_store"

    # -- A --
    @abstractmethod
    def add_from_path(self, source_file_path: str, dest_file_name: str = None, file_type: Type[File] = File) -> File:
        """Copy a file (from the path) to the store.

        :param source_file_path: path of the file to move to file store
        :type source_file_path: str
        :param dest_file_name: Name of the file once in the store. If not provided, use the source file name (make it unique if already exists) defaults to None
        :type dest_file_name: str, optional
        :param file_type: type of the file to create, defaults to File
        :type file_type: Type[File], optional
        :rtype: File
        """

        raise BadRequestException('Not implemented')

    def add_from_file(self, source_file: File, dest_file_name: str = None) -> File:
        """ Copy a file (from another file) to the store. Do nothing if the file is already in the store.
        :param source_file: file to move to file store
        :type source_file: File
        :param dest_file_name: Name of the file once in the store. If not provided, it generate a unique name, defaults to None
        :type dest_file_name: str, optional
        :rtype: File
        """

        if self.file_exists(source_file):
            return source_file
        return self.add_from_path(source_file_path=source_file.path, dest_file_name=dest_file_name,
                                  file_type=type(source_file))

    @abstractmethod
    def add_from_temp_file(
            self, source_file: Union[IOBase, SpooledTemporaryFile],
            dest_file_name: str = None, file_type: Type[File] = File) -> File:
        """[summary]

        :param source_file: [description]
        :type source_file: Union[IOBase, SpooledTemporaryFile]
        :param dest_file_name: [description], defaults to None
        :type dest_file_name: str, optional
        :param file_type: [description], defaults to File
        :type file_type: Type[File], optional
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: File
        """

        raise BadRequestException('Not implemented')

    @abstractmethod
    def create_empty(self, file_name: str, file_type: Type[File] = File) -> File:
        pass

    def file_exists(self, file: File) -> bool:
        return self.file_path_exists(file.path)

    def file_name_exists(self, file_name: str) -> bool:
        path = self._file_get_path_from_file_name(file_name)
        return self.file_path_exists(path)

    @abstractmethod
    def file_path_exists(self, file_path: str) -> bool:
        """ Return true if the file path exist in the store

        :param file_name: [description]
        :type file_name: str
        :return: [description]
        :rtype: bool
        """
        raise BadRequestException('Not implemented')

    @abstractmethod
    def _file_get_path_from_file_name(self, file_name: str) -> str:
        """return the compolete path oa a file in the store

        :param file_name: [description]
        :type file_name: str
        :rtype: str
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
    def path(self, path: str) -> None:
        """
        Set the path (or url) of the store
        """

        self.data["path"] = path
