
import os
from typing import Any, Type

from gws_core.resource.r_field import StrRField

from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator


@resource_decorator(unique_name="FsNode", hide=True)
class FSNode(Resource):
    """
    Node class to manage resources that are stored in the server (as file or folder)

    /!\ The class that extend file can only have a path and  file_store_uri attributes. Other attributes will not be
    provided when creating the resource
    """

    path: str = StrRField(searchable=True)
    file_store_uri: str = StrRField(searchable=True)

    def __init__(self, path: str = ""):
        super().__init__()
        self.path = path

    def _exists(self):
        return os.path.exists(self.path)
