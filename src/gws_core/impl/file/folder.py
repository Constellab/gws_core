

import os
from pathlib import Path
from typing import List

from ...config.config_types import ConfigParams
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ..json.json_view import JSONView
from .file_helper import FileHelper
from .fs_node import FSNode


@resource_decorator("Folder")
class Folder(FSNode):

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

    def get_default_name(self) -> str:
        return FileHelper.get_dir_name(self.path)

    def get_size(self) -> int:
        return None

    @view(view_type=JSONView, human_name="View folder content", short_description="View the sub files and folders",
          default_view=True)
    def view_as_json(self, params: ConfigParams) -> JSONView:
        return JSONView({
            "path": self.path,
            "content": FileHelper.get_dir_content_as_json(self.path)
        })
