# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os

from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.r_field.primitive_r_field import BoolRField

from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator


@resource_decorator(unique_name="FSNode", hide=True)
class FSNode(Resource):
    """
    Node class to manage resources that are stored in the server (as file or folder)

    /!\ The class that extend file can only have a path and  file_store_id attributes. Other attributes will not be
    provided when creating the resource
    """

    path: str
    file_store_id: str

    # when true, the node is considered as a symoblic link.
    # The node is not delete on resource deletion
    is_symbolic_link: bool = BoolRField(default_value=False)

    def __init__(self, path: str = ""):
        super().__init__()
        self.path = path
        self.file_store_id = None

    def get_size(self) -> int:
        return FileHelper.get_size(self.path)

    def exists(self):
        return os.path.exists(self.path)
