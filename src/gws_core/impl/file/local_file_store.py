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

from genericpath import isdir

from gws_core.impl.file.folder import Folder

from ...core.decorator.transaction import transaction
from ...core.exception.exceptions import BadRequestException
from ...core.utils.settings import Settings
from .file import File
from .file_helper import FileHelper
from .file_store import FileStore
from .fs_node import FSNode


class LocalFileStore(FileStore):
    title = "Local file store"
    description = "Storage engine to locally store files"
    _base_dir: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.path:
            self.data["path"] = os.path.join(self.get_base_dir(), self.id)

    def add_node_from_path(self, source_path: str, dest_name: str = None, node_type: Type[FSNode] = FSNode) -> FSNode:
        """
        Add a file from an external repository to a local store.

        :param source_file: The source file
        :type source_file: `str` (file path),
        :return: The file object
        :rtype: gws.file.File.
        """
        if dest_name is None:
            dest_name = FileHelper.get_name_with_extension(source_path)

        file = self._init_node(node_path=dest_name, node_type=node_type)
        self._copy_node(source_path, file.path)

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

        file: File = self._init_node(node_path=dest_file_name, node_type=file_type)
        self._init_dir(file.dir)

        with open(file.path, "wb") as buffer:
            shutil.copyfileobj(source_file, buffer)

        return file

    def create_empty_file(self, file_name: str = None, file_type: Type[File] = File) -> File:
        file: File = self._init_node(node_path=file_name, node_type=file_type)

        self._init_dir(file.dir)

        open(file.path, 'a').close()
        return file

    def create_empty_folder(self, folder_name: str, folder_type: Type[Folder] = Folder) -> Folder:
        folder: Folder = self._init_node(folder_name, folder_type)
        self._init_dir(folder.path)

        return folder

    def _copy_node(self, source: str, destination: str) -> None:
        """Copy a node from a path to another path

        :param source: [description]
        :type source: str
        :param destination: [description]
        :type destination: str
        """
        self._init_dir(str(Path(destination).parent))

        if (os.path.isdir(source)):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    def _init_dir(self, dir_: str) -> None:
        """Create the directory if it doesn't exist
        """
        # copy disk file
        if not os.path.exists(dir_):
            os.makedirs(dir_)
            if not os.path.exists(dir_):
                raise BadRequestException(f"Cannot create directory '{dir_}'")

    def _init_node(self, node_path: str = None, node_type: Type[FSNode] = FSNode) -> FSNode:

        if not isclass(node_type) or not issubclass(node_type, FSNode):
            raise BadRequestException(f"The path type '{str(node_type)}' is not a FsNode class")

        file: FSNode = node_type()
        file.path = self.get_new_node_path(node_path)
        file.file_store_id = self.id

        return file

    def get_new_node_path(self, dest_node_name: str = None) -> str:
        """Generate the node path from node name and avoid duplicate

        :param dest_file_name: [description], defaults to None
        :type dest_file_name: str, optional
        :return: [description]
        :rtype: str
        """
        # if there is no file dest, generate a name
        if dest_node_name is None or len(dest_node_name) == 0:
            time_file_name: str = str(time()).replace('.', '')
            return os.path.join(self.path, time_file_name)

        # sanitize the node name
        dest_node_name = FileHelper.sanitize_name(dest_node_name)

        #  create the node if another doesn't exists
        if not self.node_name_exists(dest_node_name):
            return os.path.join(self.path, dest_node_name)

        extension: str = FileHelper.get_extension(dest_node_name)
        file_name: str = FileHelper.get_name(dest_node_name)

        # If the file exists, find a unique name with a number
        unique: int = 1
        node_name = f"{file_name}_{unique}.{extension}" if extension else f"{file_name}_{unique}"
        while self.node_name_exists(node_name):
            unique += 1
            node_name = f"{file_name}_{unique}.{extension}" if extension else f"{file_name}_{unique}"

        return os.path.join(self.path, node_name)

    def node_path_exists(self, node_path: str) -> bool:
        # clean the file path
        node_path = str(Path(node_path))

        # Check that the file path is in the file store
        if not node_path.startswith(self.get_base_dir()):
            return False

        return os.path.exists(node_path)

    def _get_path_from_node_name(self, node_name: str) -> str:
        return os.path.join(self.path, node_name)

    @classmethod
    def drop_table(cls, *args, **kwargs):
        cls.remove_all_file_stores()
        super().drop_table(*args, **kwargs)

    @classmethod
    def get_default_instance(cls) -> 'LocalFileStore':
        file_store: FileStore = cls.select().order_by(cls.created_at).first()
        if file_store is None:
            file_store = cls()
            file_store.save()
        return file_store

    @property
    def path(self) -> str:
        """
        Get path of the local file store
        """

        return super().path

    @path.setter
    def path(self, path: str) -> None:
        """
        Locked method.
        The path of a LocalFileStore is automatically computed and cannot be manually altered.
        """

        raise BadRequestException("Cannot manually set LocalFileStore path")

    def delete_node_path(self, node_path: str) -> None:
        if self.node_path_exists(node_path):
            FileHelper.delete_node(node_path)

    @classmethod
    def get_base_dir(cls) -> str:
        if not cls._base_dir:
            settings = Settings.get_instance()
            cls._base_dir = settings.get_file_store_dir()
        return str(Path(cls._base_dir))

    @classmethod
    @transaction()
    def remove_all_file_stores(cls):
        """
        Remove all the files from the FileStore
        """

        settings = Settings.get_instance()
        if not settings.is_dev and not settings.is_test:
            raise BadRequestException("Only allowed in dev and test mode")
        file_store_list: List[FileStore] = cls.select()
        for file_store in file_store_list:
            file_store.delete_instance()

    def delete_instance(self, *args, **kwargs):
        """Override delete instance to delete all files

        :return: [description]
        :rtype: [type]
        """

        result = super().delete_instance(*args, **kwargs)

        FileHelper.delete_dir(self.path)

        return result
