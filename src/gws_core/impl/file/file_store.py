# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractclassmethod, abstractmethod
from io import IOBase
from tempfile import SpooledTemporaryFile
from typing import Any, Dict, Type, Union

from gws_core.core.model.db_field import JSONField
from gws_core.impl.file.folder import Folder

from ...core.exception.exceptions import BadRequestException
from ...core.model.model import Model
from .file import File
from .fs_node import FSNode


class FileStore(Model):
    """
    FileStore class
    """

    data: Dict[str, Any] = JSONField(null=True)

    _table_name = "gws_file_store"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved() and not self.data:
            self.data = {}

    @abstractmethod
    def add_node_from_path(self, source_path: str, dest_name: str = None, node_type: Type[FSNode] = FSNode) -> FSNode:
        """Copy a node (file or directory) from the path to the store.

        :param source_file_path: path of the file or directory to move to file store
        :type source_file_path: str
        :param dest_file_name: Name of the file or directory once in the store. If not provided, use the source node name (make it unique if already exists) defaults to None
        :type dest_file_name: str, optional
        :param file_type: type of the node to create, defaults to FsNode
        :type node_type: Type[FsNode], optional
        :rtype: File
        """

        raise BadRequestException('Not implemented')

    def add_file_from_path(
            self, source_file_path: str, dest_file_name: str = None, file_type: Type[File] = File) -> File:
        """Copy a file (from the path) to the store.

        :param source_file_path: path of the file to move to file store
        :type source_file_path: str
        :param dest_file_name: Name of the file once in the store. If not provided, use the source file name (make it unique if already exists) defaults to None
        :type dest_file_name: str, optional
        :param file_type: type of the file to create, defaults to File
        :type file_type: Type[File], optional
        :rtype: File
        """
        return self.add_node_from_path(source_file_path, dest_file_name, file_type)

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
    def create_empty_file(self, file_name: str, file_type: Type[File] = File) -> File:
        pass

    @abstractmethod
    def create_empty_folder(self, folder_name: str, folder_type: Type[Folder] = Folder) -> Folder:
        pass

    @abstractmethod
    def delete_node_path(self, node_path: str) -> None:
        pass

    def delete_node(self, node: FSNode) -> None:
        self.delete_node_path(node.path)

    def node_exists(self, node: FSNode) -> bool:
        return self.node_path_exists(node.path)

    def node_name_exists(self, node_name: str) -> bool:
        path = self._get_path_from_node_name(node_name)
        return self.node_path_exists(path)

    @abstractmethod
    def node_path_exists(self, node_path: str) -> bool:
        """ Return true if the node path exist in the store

        :param file_name: [description]
        :type file_name: str
        :return: [description]
        :rtype: bool
        """
        raise BadRequestException('Not implemented')

    @abstractmethod
    def _get_path_from_node_name(self, node_name: str) -> str:
        """return the complete path of a node in the store

        :param file_name: [description]
        :type file_name: str
        :rtype: str
        """
        raise BadRequestException('Not implemented')

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

    @property
    def path(self) -> str:
        """
        Get path (or url) of the store
        """

        return self.data.get("path", "")

    @path.setter
    def path(self, path: str) -> None:
        """
        Set the path (or url) of the store
        """

        self.data["path"] = path

    @classmethod
    def get_default_instance(cls) -> 'FileStore':
        from .local_file_store import LocalFileStore
        return LocalFileStore.get_default_instance()

    class Meta:
        table_name = 'gws_file_store'
