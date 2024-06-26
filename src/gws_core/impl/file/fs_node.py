

import os
from abc import abstractmethod
from pathlib import PosixPath

from gws_core.impl.file.file_helper import FileHelper
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import BoolRField, StrRField

from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator


@resource_decorator(unique_name="FSNode", hide=True,
                    style=TypingStyle.material_icon("folder", background_color="#7b9dd2"))
class FSNode(Resource):
    """
    Node class to manage resources that are stored in the server (as file or folder)

    ## Technical notes:
    /!\ The class that extend file can only have a path and  file_store_id attributes. Other attributes will not be
    provided when creating the resource
    """

    path: str = StrRField(searchable=True)
    file_store_id: str = StrRField(searchable=True)

    # when true, the node is considered as a symoblic link.
    # The node is not delete on resource deletion
    is_symbolic_link: bool = BoolRField(default_value=False)

    def __init__(self, path: str = ""):
        """ Create a new FSNode

        :param path: absolute path to the file, defaults to ""
        :type path: str, optional
        """
        super().__init__()

        if path is None:
            raise ValueError("The path cannot be None")

        if not isinstance(path, str) and not isinstance(path, PosixPath):
            raise ValueError("The path must be a string")

        self.path = str(path)
        self.file_store_id = None

    def get_size(self) -> int:
        return FileHelper.get_size(self.path)

    def exists(self):
        return os.path.exists(self.path)

    @abstractmethod
    def copy_to_path(self, destination: str) -> str:
        """
        Copy the file or folder to the destination and rename the base name

        :param destination: complete path to the destination
        :type destination: str
        :return: the new path
        :rtype: str
        """

    def copy_to_directory(self, destination: str) -> str:
        """
        Copy the node to the directory and keep the same base name

        :param destination: the destination directory
        :type destination: str
        """
        return self.copy_to_path(os.path.join(destination, self.get_base_name()))

    @abstractmethod
    def get_base_name(self) -> str:
        """
        Get the name of the file or folder without the path
        """

    def get_default_name(self) -> str:
        return self.get_base_name()
