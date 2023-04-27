# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from pathlib import Path
from typing import List

from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.file.file import File
from gws_core.impl.file.folder_view import LocalFolderView
from gws_core.resource.view.view import View

from ...config.config_types import ConfigParams
from ...resource.resource_decorator import resource_decorator
from ...resource.view.view_decorator import view
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

    @view(view_type=LocalFolderView, human_name="View folder content",
          short_description="View the sub files and folders", default_view=True)
    def view_as_json(self, params: ConfigParams) -> LocalFolderView:
        return LocalFolderView(self.path)

    @view(view_type=View, human_name="View folder content",
          short_description="View the sub files and folders", specs={
              'sub_file_path': StrParam()
          })
    def view_sub_file(self, params: ConfigParams) -> View:
        complete_path = os.path.join(self.path, params['sub_file_path'])

        if not FileHelper.exists_on_os(complete_path):
            raise BadRequestException("The file does not exist")

        if not FileHelper.is_file(complete_path):
            raise BadRequestException("The path is not a file")

        sub_file = File(complete_path)
        return sub_file.default_view(ConfigParams({}))
