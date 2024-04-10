

import os
from pathlib import Path
from typing import List

from gws_core.config.param.param_spec import IntParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.file.file import File
from gws_core.impl.file.folder_view import LocalFolderView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.view.view import View

from ...config.config_params import ConfigParams
from ...resource.resource_decorator import resource_decorator
from ...resource.view.view_decorator import view
from .file_helper import FileHelper
from .fs_node import FSNode


@resource_decorator("Folder", human_name="Folder",
                    style=TypingStyle.material_icon("folder"))
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

    def get_sub_path(self, sub_node_path: str) -> str:
        """Get the path of a sub node, in the folder
        """
        return os.path.join(self.path, sub_node_path)

    def get_sub_node(self, sub_node_path: str) -> FSNode:
        """Get the sub node of this folder, with the given path
        """
        sub_node_path = self.get_sub_path(sub_node_path)

        if not FileHelper.exists_on_os(sub_node_path):
            raise BadRequestException("The sub node does not exist")

        if FileHelper.is_file(sub_node_path):
            return File(sub_node_path)
        else:
            return Folder(sub_node_path)

    def copy_to_path(self, destination: str) -> str:
        """Copy this folder to the given destination
        """
        FileHelper.copy_dir(self.path, destination)
        return destination

    def get_base_name(self) -> str:
        return FileHelper.get_dir_name(self.path)

    @view(view_type=LocalFolderView, human_name="View folder content",
          short_description="View the sub files and folders", default_view=True)
    def view_as_json(self, params: ConfigParams) -> LocalFolderView:
        return LocalFolderView(self.path)

    @view(view_type=View, human_name="View folder content",
          short_description="View the sub files and folders", specs={
              'sub_file_path': StrParam(),
              "line_number": IntParam(default_value=1, min_value=1, human_name="From line")
          })
    def view_sub_file(self, params: ConfigParams) -> View:
        complete_path = os.path.join(self.path, params['sub_file_path'])

        if not FileHelper.exists_on_os(complete_path):
            raise BadRequestException("The file does not exist")

        if not FileHelper.is_file(complete_path):
            raise BadRequestException("The path is not a file")

        sub_file = File(complete_path)
        view = sub_file.get_default_view(params.get('line_number', 1))
        view.set_title(sub_file.get_default_name())
        return view
