

import os
from pathlib import Path
from typing import List

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import IntParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.settings import Settings
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
    """
    Resource that represents a folder in the system.


    ## Technical notes:
    /!\ The class that extend folder can only have a path and  file_store_id attributes. Other attributes will not be
    provided when creating the resource.
    """

    def __init__(self, path: str = ""):
        """ Create a new Folder

        :param path: absolute path to the folder, defaults to ""
        :type path: str, optional
        """
        super().__init__(path)
        if self.exists() and not FileHelper.is_dir(self.path):
            raise BadRequestException(f"The path {self.path} is not a folder")

    def has_node(self, sub_node_path: str) -> bool:
        """
        Check if the sub node exists

        :param sub_node_path: relative path of the sub node
        :type sub_node_path: str
        :return: True if the sub node exists
        :rtype: bool
        """
        return FileHelper.exists_on_os(self.get_sub_path(sub_node_path))

    def create_empty_file_if_not_exist(self, file_path: str) -> Path:
        """
        Create an empty file inside this folder if it does not exist.
        Creates intermediate directories if needed.

        :param file_path: relative path of the file
        :type file_path: str
        :return: the path of the file
        :rtype: Path
        """
        return FileHelper.create_empty_file_if_not_exist(self.get_sub_path(file_path))

    def create_dir_if_not_exist(self, dir_path: str) -> Path:
        """
        Create a directory inside this folder if it does not exist.
        Creates intermediate directories if needed.

        :param dir_name: relative path of the directory
        :type dir_name: str
        :return: the path of the directory
        :rtype: Path
        """
        return FileHelper.create_dir_if_not_exist(self.get_sub_path(dir_path))

    def list_dir(self) -> List[str]:
        """
        List the files and directories inside this folder (not recursive)

        :return: List of files and directories
        :rtype: List[str]
        """
        return os.listdir(self.path)

    def list_dir_path(self) -> List[str]:
        """
        List the files and directories absolute path inside this folder (not recursive)

        :return: List of absolute path files and directories
        :rtype: List[str]
        """
        return list(map(self.get_sub_path,  self.list_dir()))

    def list_all_file_paths(self) -> List[str]:
        """
        List the files inside this folder recursively

        :return: List of all file paths in the folder
        :rtype: List[str]
        """
        file_paths = []
        for root, _, files in os.walk(self.path):
            for file in files:
                file_paths.append(os.path.join(root, file))
        return file_paths

    def get_sub_path(self, sub_node_path: str) -> str:
        """
        Get the absolute path of the sub node

        :param sub_node_path: relative path of the sub node
        :type sub_node_path: str
        :return: the absolute path of the sub node
        :rtype: str
        """
        return os.path.join(self.path, sub_node_path)

    def get_sub_node(self, sub_node_path: str) -> FSNode:
        """
        Get the sub node (file or folder) at the given path as a FSNode

        :param sub_node_path: relative path of the sub node
        :type sub_node_path: str
        :raises BadRequestException: If the sub node does not exist
        :return: the sub node
        :rtype: FSNode
        """
        sub_node_path = self.get_sub_path(sub_node_path)

        if not FileHelper.exists_on_os(sub_node_path):
            raise BadRequestException("The sub node does not exist")

        if FileHelper.is_file(sub_node_path):
            return File(sub_node_path)
        else:
            return Folder(sub_node_path)

    def rename_sub_node(self, sub_node_path: str, new_name: str) -> None:
        """
        Rename the sub node (file or folder) at the given path

        :param sub_node_path: relative path of the sub node
        :type sub_node_path: str
        :param new_name: new name of the sub node
        :type new_name: str
        :raises BadRequestException: If the sub node does not exist
        """
        sub_node_path = self.get_sub_path(sub_node_path)

        if not FileHelper.exists_on_os(sub_node_path):
            raise BadRequestException("The sub node does not exist")

        new_sub_node_path = self.get_sub_path(new_name)

        if FileHelper.exists_on_os(new_sub_node_path):
            raise BadRequestException("The new name already exists in the folder")

        FileHelper.move_file_or_dir(sub_node_path, new_sub_node_path)

    def delete_sub_node(self, sub_node_path: str,
                        ignore_errors: bool = True) -> None:
        """
        Delete the sub node (file or folder) at the given path

        :param sub_node_path: relative path of the sub node
        :type sub_node_path: str
        :param ignore_errors: if True, errors will be ignored, defaults to True
        :type ignore_errors: bool, optional
        :raises BadRequestException: If the sub node does not exist
        """
        sub_node_path = self.get_sub_path(sub_node_path)

        FileHelper.delete_node(sub_node_path, ignore_errors)

    def empty_folder(self) -> None:
        """
        Empty the folder content. This will delete all files and sub folders inside this folder.
        The folder itself will not be deleted.
        """
        FileHelper.delete_dir_content(self.path)

    @view(view_type=LocalFolderView, human_name="View folder content",
          short_description="View the sub files and folders", default_view=True)
    def view_as_json(self, params: ConfigParams) -> LocalFolderView:
        return LocalFolderView(self.path)

    @view(view_type=View, human_name="View folder content",
          short_description="View the sub files and folders", specs=ConfigSpecs({
              'sub_file_path': StrParam(),
              "line_number": IntParam(default_value=1, min_value=1, human_name="From line")
          }))
    def view_sub_file(self, params: ConfigParams) -> View:
        complete_path = os.path.join(self.path, params['sub_file_path'])

        if not FileHelper.exists_on_os(complete_path):
            raise BadRequestException("The file does not exist")

        if not FileHelper.is_file(complete_path):
            raise BadRequestException("The path is not a file")

        sub_file = File(complete_path)
        view_ = sub_file.get_default_view(params.get('line_number', 1))
        view_.set_title(sub_file.get_base_name())
        return view_

    @staticmethod
    def new_temp_folder() -> 'Folder':
        """
        Create a new temporary folder. The folder will be created in the system temporary directory.
        If this resource is then saved, it will be moved to the file store.

        :return: a new temporary folder
        :rtype: Folder
        """
        temp_folder_path = Settings.make_temp_dir()
        return Folder(temp_folder_path)
