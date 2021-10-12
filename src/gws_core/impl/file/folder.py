

import os
from pathlib import Path
from posixpath import dirname
from typing import List

from ...impl.file.file_helper import FileHelper
from ...resource.resource_decorator import resource_decorator
from .fs_node import FSNode


@resource_decorator("Folder")
class Folder(FSNode):

    @property
    def name(self):
        return os.path.basename(self.path)

    def has_node(self, node_name: str) -> bool:
        return FileHelper.exists_on_os(self.get_sub_path(node_name))

    def create_empty_file_if_not_exist(self, file_name: str) -> Path:
        return FileHelper.create_empty_file_if_not_exist(self.get_sub_path(file_name))

    def create_dir_if_not_exist(self, dir_name: str) -> Path:
        return FileHelper.create_dir_if_not_exist(self.get_sub_path(dir_name))

    def list_dir(self) -> List[str]:
        """Return the name of files and directories inside this folder
        """
        return os.listdir(self.path)

    def list_dir_path(self) -> List[str]:
        """Return the path of files and directories inside this folder
        """
        return list(map(self.get_sub_path,  self.list_dir()))

    def get_sub_path(self, node_name: str) -> str:
        """Get the path of a sub node, in the folder
        """
        return os.path.join(self.path, node_name)
