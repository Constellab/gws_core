# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractclassmethod, abstractmethod
from io import IOBase
from tempfile import SpooledTemporaryFile
from typing import Union

from ...core.exception.exceptions import BadRequestException
from ...core.model.model import Model
from ...model.typing_register_decorator import typing_registrator
from .file_resource import File

# ####################################################################
#
# FileStore class
#
# ####################################################################


@typing_registrator(unique_name="FileStore", object_type="GWS_CORE", hide=True)
class FileStore(Model):
    """
    FileStore class
    """
    title = "File store"
    description = ""
    _table_name = "gws_file_store"

    # -- A --
    @abstractmethod
    def add_from_path(self, source_file: str, dest_file_name: str = None) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `str` (file path),
        :return: The file object
        :rtype: gws.file.File.
        """

        raise BadRequestException('Not implemented')

    @abstractmethod
    def add_from_file(self, source_file: File, dest_file_name: str = None) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `File`
        :return: The file object
        :rtype: gws.file.File.
        """

        raise BadRequestException('Not implemented')

    @abstractmethod
    def add_from_temp_file(self, source_file: Union[IOBase, SpooledTemporaryFile], dest_file_name: str = None) -> File:
        """
        Add a file from an external repository to a local store. Must be implemented by the child class.

        :param source_file: The source file
        :type source_file: `IOBase` or `SpooledTemporaryFile`
        :return: The file object
        :rtype: gws.file.File.
        """

        raise BadRequestException('Not implemented')

    @abstractmethod
    def file_exists(self, file_name: str) -> bool:
        pass

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
