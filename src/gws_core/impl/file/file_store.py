from abc import abstractmethod
from io import IOBase
from tempfile import SpooledTemporaryFile
from typing import Any, cast

from gws_core.core.model.db_field import JSONField

from ...core.exception.exceptions import BadRequestException
from ...core.model.model import Model
from .file import File
from .fs_node import FSNode


class FileStore(Model):
    """
    FileStore class
    """

    data: dict[str, Any] = JSONField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved() and not self.data:
            self.data = {}

    @abstractmethod
    def add_node_from_path(
        self, source_path: str, dest_name: str | None = None, node_type: type[FSNode] | None = None
    ) -> FSNode:
        """Copy a node (file or directory) from the path to the store.

        :param source_file_path: path of the file or directory to move to file store
        :type source_file_path: str
        :param dest_file_name: Name of the file or directory once in the store. If not provided, use the source node name (make it unique if already exists) defaults to None
        :type dest_file_name: str, optional
        :param file_type: type of the node to create, defaults to None
        :type node_type: Type[FsNode], optional
        :rtype: File
        """

        raise BadRequestException("Not implemented")

    def add_file_from_path(
        self, source_file_path: str, dest_file_name: str | None = None, file_type: type[File] = File
    ) -> File:
        """Copy a file (from the path) to the store.

        :param source_file_path: path of the file to move to file store
        :type source_file_path: str
        :param dest_file_name: Name of the file once in the store. If not provided, use the source file name (make it unique if already exists) defaults to None
        :type dest_file_name: str, optional
        :param file_type: type of the file to create, defaults to File
        :type file_type: Type[File], optional
        :rtype: File
        """
        return cast(File, self.add_node_from_path(source_file_path, dest_file_name, file_type))

    @abstractmethod
    def add_from_temp_file(
        self,
        source_file: IOBase | SpooledTemporaryFile,
        dest_file_name: str | None = None,
        file_type: type[File] = File,
    ) -> File:
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

        raise BadRequestException("Not implemented")

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
        """Return true if the node path exist in the store

        :param file_name: [description]
        :type file_name: str
        :return: [description]
        :rtype: bool
        """
        raise BadRequestException("Not implemented")

    @abstractmethod
    def get_node_by_path(
        self, node_path: str | None = None, node_type: type[FSNode] | None = None
    ) -> FSNode:
        """Get a node by its path

        :param node_path: _description_, defaults to None
        :type node_path: str, optional
        :param node_type: _description_, defaults to FSNode
        :type node_type: Type[FSNode], optional
        :raises BadRequestException: _description_
        :return: _description_
        :rtype: FSNode
        """

    @abstractmethod
    def _get_path_from_node_name(self, node_name: str) -> str:
        """return the complete path of a node in the store

        :param file_name: [description]
        :type file_name: str
        :rtype: str
        """
        raise BadRequestException("Not implemented")

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
    def get_default_instance(cls) -> "FileStore":
        from .local_file_store import LocalFileStore

        return LocalFileStore.get_default_instance()

    class Meta:
        table_name = "gws_file_store"
        is_table = True
